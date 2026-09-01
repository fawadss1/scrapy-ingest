"""Logging extension for capturing full job logs into the shared collector."""
from __future__ import annotations

import logging

from scrapy import signals

from ..collector import ensure_collector
from ..config.settings import Settings
from .log_handler import IngestLogHandler, capture_prints, drain_early, stop_prints


class LoggingExtension:
    """
    Capture full job logs (startup → crawl → stats dump → closed)
    plus print() spider lines into the shared collector.
    """

    def __init__(self, crawler, level=logging.INFO):
        self.crawler = crawler
        self.settings = Settings(crawler.settings)
        self.collector = ensure_collector(crawler)
        drain_early(self.collector, min_level=level)
        self.handler = IngestLogHandler(self.collector, level=level)
        root = logging.getLogger()
        if self.handler not in root.handlers:
            root.addHandler(self.handler)
        if root.level == logging.NOTSET or root.level > level:
            root.setLevel(level)
        for name in ("scrapy", "twisted", "py.warnings"):
            logging.getLogger(name).propagate = True
        capture_prints(self.collector)
        crawler.signals.connect(self.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(self.engine_stopped, signal=signals.engine_stopped)

    @classmethod
    def from_crawler(cls, crawler):
        if getattr(crawler, "_ingest_logging_ext", None) is not None:
            return crawler._ingest_logging_ext

        name = crawler.settings.get("LOG_LEVEL", "INFO")
        level = logging._nameToLevel.get(str(name).upper(), logging.INFO)
        ext = cls(crawler, level)
        crawler._ingest_logging_ext = ext
        return ext

    def spider_opened(self, spider):
        from ..database.flusher import get_flusher

        get_flusher(self.crawler, self.settings).start(spider)

    def engine_stopped(self):
        def _done():
            root = logging.getLogger()
            if self.handler in root.handlers:
                root.removeHandler(self.handler)
            stop_prints()

        try:
            from twisted.internet import reactor

            reactor.addSystemEventTrigger("before", "shutdown", _done)
        except Exception:
            _done()
