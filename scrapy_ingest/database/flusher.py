"""Shared flusher: batch collector data into SQL and/or search indexes."""
import logging

from scrapy import signals
from twisted.internet import task

from ..collector import ensure_collector
from ..config.settings import validate_settings
from ..exceptions import IngestConnectionError, IngestError
from .search import SearchClient, SearchWriter
from ..utils.console import info
from ..utils.serialization import json_safe
from ..utils.summary import display_database, format_crawl_summary
from .connection import DatabaseConnection
from .schema import SchemaManager
from .writer import DbWriter

logger = logging.getLogger(__name__)


def get_flusher(crawler, settings):
    """Return the crawler's shared IngestFlusher, creating it if needed."""
    if getattr(crawler, "_ingest_flusher", None) is None:
        flusher = IngestFlusher(crawler, settings)
        crawler._ingest_flusher = flusher
        crawler.signals.connect(flusher.engine_stopped, signal=signals.engine_stopped)
    return crawler._ingest_flusher


class IngestFlusher:
    """Flush the collector to Postgres/MySQL, Elasticsearch/OpenSearch, or both."""

    def __init__(self, crawler, settings):
        self.crawler = crawler
        self.settings = settings
        self.collector = ensure_collector(crawler)
        self.db = None
        self.db_writer = None
        self.search_client = None
        self.search_writer = None
        self.job_id = None
        self.job_pk = None
        self.spider_name = None
        self.periodic_task = None
        self._started = False
        self._done = False
        self._summary_printed = False

    def _use_db(self):
        return self.settings.ingest_to_database

    def _use_search(self):
        return self.settings.ingest_to_search

    def start(self, spider):
        if self._started:
            return
        self._started = True
        validate_settings(self.settings)

        self.job_id = self.settings.get_identifier_value(spider)
        self.spider_name = getattr(spider, "name", None)

        if self._use_db():
            self.db = DatabaseConnection(self.settings.db_url)
            if not self.db.connect():
                raise IngestConnectionError("Failed to connect to database")
            schema = SchemaManager(self.db, self.settings)
            schema.ensure_tables_exist()
            self.db_writer = DbWriter(self.db, self.settings)
            self.job_pk = self.db_writer.start_job(self.job_id, spider)

        if self._use_search():
            self.search_client = SearchClient(self.settings)
            self.search_client.ping()
            self.search_writer = SearchWriter(self.search_client, self.settings)
            self.search_writer.start_job(self.job_id, spider)

        logger.info(
            "Ingest job job_id=%s pk=%s spider=%s db=%s search=%s",
            self.job_id,
            self.job_pk,
            spider.name,
            self._use_db(),
            self._use_search(),
        )

        interval = self.settings.ingest_flush_interval
        if interval > 0:
            self.periodic_task = task.LoopingCall(self._tick)
            self.periodic_task.start(interval, now=False)

    def _tick(self):
        if self.collector.has_data():
            self.flush()

    def flush(self, spider=None):
        if not self.db_writer and not self.search_writer:
            return
        data = self.collector.get_and_clear()
        if not data:
            return

        if spider is not None and self.job_id is None:
            self.job_id = self.settings.get_identifier_value(spider)
            self.spider_name = getattr(spider, "name", None)

        if self.db_writer and self.job_pk is None and spider is not None:
            self.job_pk = self.db_writer.start_job(self.job_id, spider)

        try:
            if self.db_writer:
                self.db_writer.write(data, self.job_pk)
            if self.search_writer:
                self.search_writer.write(data, self.job_id)
        except IngestError:
            logger.exception("Failed to flush ingest batch; requeuing data")
            self.collector.requeue(data)
        except Exception:
            logger.exception("Failed to flush ingest batch; requeuing data")
            self.collector.requeue(data)

    def stop_periodic(self):
        if self.periodic_task and self.periodic_task.running:
            self.periodic_task.stop()
        self.periodic_task = None

    def _close_clients(self):
        if self.db:
            self.db.close()
            self.db = None
        if self.search_client:
            self.search_client.close()
            self.search_client = None

    def _finalize_job(self):
        if not self.job_id:
            return
        metrics = None
        try:
            stats = None
            crawler = self.crawler
            if crawler is not None and getattr(crawler, "stats", None) is not None:
                stats = json_safe(crawler.stats.get_stats())
            reason = getattr(crawler, "ingest_finish_reason", None) if crawler else None
            if self.db_writer and self.job_pk is not None:
                metrics = self.db_writer.finish_job(
                    self.job_pk, reason=reason, stats=stats
                )
            if self.search_writer:
                search_metrics = self.search_writer.finish_job(
                    self.job_id, reason=reason, stats=stats
                )
                metrics = metrics or search_metrics
            if metrics:
                self._print_summary(metrics)
        except Exception:
            logger.exception("Failed to finalize ingest job %s", self.job_id)

    def _print_summary(self, metrics):
        if self._summary_printed or not metrics:
            return
        if not getattr(self.settings, "ingest_show_summary", True):
            return
        self._summary_printed = True
        spider = self.spider_name
        if not spider and self.crawler is not None:
            spider = getattr(getattr(self.crawler, "spider", None), "name", None)
        settings = self.settings
        info(
            format_crawl_summary(
                {
                    "job_id": self.job_id,
                    "spider": spider,
                    "database": display_database(settings.db_url)
                    if settings.ingest_to_database
                    else "-",
                    "search": display_database(settings.search_url)
                    if settings.ingest_to_search
                    else "-",
                    "jobs_table": settings.db_jobs_table,
                    "items_table": settings.db_items_table,
                    "requests_table": settings.db_requests_table,
                    "logs_table": settings.db_logs_table,
                    **metrics,
                }
            )
        )

    def _shutdown(self):
        self.flush()
        self._finalize_job()
        self._close_clients()

    def engine_stopped(self):
        if self._done:
            return
        self._done = True
        self.stop_periodic()
        self.flush()
        self._finalize_job()
        try:
            from twisted.internet import reactor

            reactor.addSystemEventTrigger("before", "shutdown", self._shutdown)
        except Exception:
            self._shutdown()
