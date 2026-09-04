"""Bulk index ingest batches to Elasticsearch or OpenSearch."""
import logging
from datetime import datetime

from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk as os_bulk

from ..exceptions import IngestConnectionError
from ..utils.serialization import json_safe
from ..utils.time import get_current_datetime

logger = logging.getLogger(__name__)


class SearchClient:
    """OpenSearch client wrapper (Elasticsearch-compatible REST API)."""

    def __init__(self, settings):
        url = settings.search_url.rstrip("/")
        kwargs = {
            "verify_certs": settings.search_ssl_verify,
            "ssl_show_warn": settings.search_ssl_verify,
            "use_ssl": url.startswith("https://"),
        }
        if settings.search_user:
            kwargs["http_auth"] = (settings.search_user, settings.search_password or "")

        self._bulk = os_bulk
        self._client = OpenSearch(hosts=[url], **kwargs)
        self._ready = set()

    def ping(self):
        if not self._client.ping():
            raise IngestConnectionError("Search cluster did not respond to ping")

    def close(self):
        self._client.close()

    def ensure_index(self, name):
        if name in self._ready:
            return
        if not self._client.indices.exists(index=name):
            self._client.indices.create(index=name)
        self._ready.add(name)

    def index(self, index, doc_id, doc):
        self.ensure_index(index)
        self._client.index(index=index, id=doc_id, body=json_safe(doc))

    def bulk(self, index, docs):
        if not docs:
            return
        self.ensure_index(index)
        actions = ({"_index": index, "_source": json_safe(doc)} for doc in docs)
        _, errors = self._bulk(self._client, actions, raise_on_error=False)
        if errors:
            logger.warning("Search bulk had %s error(s)", len(errors))


class SearchWriter:
    """Index collector batches into search indexes."""

    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self._counts = {
            "items_count": 0,
            "requests_count": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "logs_count": 0,
            "errors_count": 0,
        }
        self._started_at = None

    def _index(self, table):
        return f"{self.settings.search_index_prefix}-{table}"

    @staticmethod
    def _iso(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def start_job(self, job_key, spider):
        self._started_at = get_current_datetime(self.settings)
        self._counts = {key: 0 for key in self._counts}
        self.client.index(
            self._index(self.settings.db_jobs_table),
            job_key,
            {
                "job_id": job_key,
                "spider_name": getattr(spider, "name", None),
                "status": "running",
                "started_at": self._iso(self._started_at),
            },
        )
        return job_key

    def write(self, data, job_key):
        created_at = get_current_datetime(self.settings)
        stamp = self._iso(created_at)
        items = [
            {"job_id": job_key, "item": item, "created_at": stamp}
            for item in (data.get("items") or [])
        ]
        requests = [
            {
                "job_id": job_key,
                "url": req.get("url"),
                "method": req.get("method"),
                "status_code": req.get("status_code"),
                "response_time_secs": req.get("response_time_secs"),
                "fingerprint": req.get("fingerprint"),
                "parent_url": req.get("parent_url"),
                "error": req.get("error"),
                "success": req.get("success"),
                "created_at": stamp,
            }
            for req in (data.get("requests") or [])
        ]
        logs = [
            {
                "job_id": job_key,
                "time": self._iso(entry.get("time")),
                "level": entry.get("level"),
                "logger": entry.get("logger"),
                "message": entry.get("message"),
                "exception": entry.get("exception"),
            }
            for entry in (data.get("logs") or [])
        ]
        self.client.bulk(self._index(self.settings.db_items_table), items)
        self.client.bulk(self._index(self.settings.db_requests_table), requests)
        self.client.bulk(self._index(self.settings.db_logs_table), logs)
        self._counts["items_count"] += len(items)
        self._counts["requests_count"] += len(requests)
        self._counts["success_requests"] += sum(1 for req in requests if req.get("success"))
        self._counts["failed_requests"] += sum(
            1 for req in requests if req.get("success") is False
        )
        log_errors = sum(
            1 for entry in logs if entry.get("level") in ("ERROR", "CRITICAL")
        )
        self._counts["logs_count"] += len(logs)
        self._counts["errors_count"] = self._counts["failed_requests"] + log_errors
        self._save_job(job_key)

    def _elapsed(self, end_time=None):
        end = end_time or get_current_datetime(self.settings)
        if self._started_at is None:
            return 0.0, 0.0
        elapsed = max((end - self._started_at).total_seconds(), 0.0)
        if elapsed <= 0:
            return 0.0, 0.0
        return round(elapsed, 2), round(self._counts["items_count"] / elapsed * 60, 2)

    def _save_job(self, job_key, end_time=None, **extra):
        elapsed, rate = self._elapsed(end_time)
        self.client.index(
            self._index(self.settings.db_jobs_table),
            job_key,
            {
                "job_id": job_key,
                "started_at": self._iso(self._started_at),
                **self._counts,
                "elapsed_seconds": elapsed,
                "items_per_min": rate,
                **extra,
            },
        )

    def finish_job(self, job_key, reason=None, stats=None):
        finished_at = get_current_datetime(self.settings)
        if stats and not reason:
            reason = stats.get("finish_reason")
        elapsed, rate = self._elapsed(finished_at)
        self._save_job(
            job_key,
            end_time=finished_at,
            status="finished",
            finished_at=self._iso(finished_at),
            finish_reason=reason,
            stats=json_safe(stats) if stats else None,
        )
        return {
            **self._counts,
            "elapsed_seconds": elapsed,
            "items_per_min": rate,
            "reason": reason,
        }
