"""Shared flusher: batch collector data into PostgreSQL."""
import logging

from scrapy import signals
from twisted.internet import task

from ..collector import ensure_collector
from ..config.settings import validate_settings
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
    """
    Connects to Postgres, creates tables, and flushes the collector
    on batch size, a periodic timer, and engine stop.
    """

    def __init__(self, crawler, settings):
        self.crawler = crawler
        self.settings = settings
        self.collector = ensure_collector(crawler)
        self.db = None
        self.writer = None
        self.job_id = None
        self.job_pk = None
        self.spider_name = None
        self.periodic_task = None
        self._started = False
        self._done = False
        self._summary_printed = False

    def start(self, spider):
        if self._started:
            return
        self._started = True
        validate_settings(self.settings)

        self.db = DatabaseConnection(self.settings.db_url)
        if not self.db.connect():
            raise Exception("Failed to connect to database")

        schema = SchemaManager(self.db, self.settings)
        schema.ensure_tables_exist()

        self.writer = DbWriter(self.db, self.settings)
        self.job_id = self.settings.get_identifier_value(spider)
        self.spider_name = getattr(spider, "name", None)
        self.job_pk = self.writer.start_job(self.job_id, spider)
        logger.info(
            "Ingest job pk=%s job_id=%s spider=%s",
            self.job_pk,
            self.job_id,
            spider.name,
        )

        interval = self.settings.ingest_flush_interval
        if interval > 0:
            self.periodic_task = task.LoopingCall(self._tick)
            self.periodic_task.start(interval, now=False)

    def _tick(self):
        if self.collector.has_data():
            self.flush()

    def flush(self, spider=None):
        if self.writer is None:
            return
        data = self.collector.get_and_clear()
        if not data:
            return

        job_pk = self.job_pk
        if job_pk is None and spider is not None:
            self.job_id = self.settings.get_identifier_value(spider)
            self.spider_name = getattr(spider, "name", None)
            job_pk = self.writer.start_job(self.job_id, spider)
            self.job_pk = job_pk

        try:
            self.writer.write(data, job_pk)
        except Exception:
            logger.exception("Failed to flush ingest batch; requeuing data")
            self.collector.requeue(data)

    def stop_periodic(self):
        if self.periodic_task and self.periodic_task.running:
            self.periodic_task.stop()
        self.periodic_task = None

    def _close_db(self):
        if self.db:
            self.db.close()
            self.db = None

    def _finalize_job(self):
        if not self.writer or self.job_pk is None:
            return
        try:
            stats = None
            crawler = self.crawler
            if crawler is not None and getattr(crawler, "stats", None) is not None:
                stats = json_safe(crawler.stats.get_stats())
            reason = getattr(crawler, "ingest_finish_reason", None) if crawler else None
            metrics = self.writer.finish_job(self.job_pk, reason=reason, stats=stats)
            self._print_summary(metrics)
        except Exception:
            logger.exception("Failed to finalize jobs row for pk=%s", self.job_pk)

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
                    "database": display_database(getattr(settings, "db_url", None)),
                    "jobs_table": getattr(settings, "db_jobs_table", None),
                    "items_table": getattr(settings, "db_items_table", None),
                    "requests_table": getattr(settings, "db_requests_table", None),
                    "logs_table": getattr(settings, "db_logs_table", None),
                    **metrics,
                }
            )
        )

    def _shutdown(self):
        self.flush()
        self._finalize_job()
        self._close_db()

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
