"""Enable all ingest components from a single entry point (the item pipeline)."""

import inspect

from scrapy.core.engine import ExecutionEngine
from scrapy.core.scraper import Scraper

from ..collector import ensure_collector
from ..extensions.logging import LoggingExtension
from ..extensions.stats import StatsExtension
from ..extensions.request_logger import RequestLogger
from ..middleware import ErrorMiddleware, _inject_into_scraper
from ..utils.updates import update_available


def _inject_error_middleware(crawler, engine=None):
    if getattr(crawler, "_ingest_error_mw_hooked", False):
        return
    try:
        engine = engine or crawler.engine
        mwman = engine.downloader.middleware
    except (AttributeError, RuntimeError):
        return

    mw = ErrorMiddleware()
    mw.crawler = crawler
    mw.collector = crawler.ingest_collector
    mwman._add_middleware(mw)
    crawler._ingest_error_mw_hooked = True


def _find_building(cls):
    """Find an in-progress constructor instance of *cls* on the call stack."""
    for frame_info in inspect.stack()[1:]:
        obj = frame_info.frame.f_locals.get("self")
        if isinstance(obj, cls):
            return obj
    return None


def attach_runtime_hooks(crawler):
    """
    Attach parent_url + error hooks.

    ITEM_PIPELINES load inside Scraper.__init__ (before crawler.engine is set),
    so we locate the in-progress Scraper/Engine on the stack and patch those.
    """
    if not hasattr(crawler, "ingest_parent_by_fp"):
        crawler.ingest_parent_by_fp = {}

    scraper = _find_building(Scraper)
    if scraper is not None:
        _inject_into_scraper(crawler, scraper)
    else:
        try:
            _inject_into_scraper(crawler, crawler.engine.scraper)
        except (AttributeError, RuntimeError):
            pass

    engine = _find_building(ExecutionEngine)
    if engine is not None and getattr(engine, "downloader", None) is not None:
        _inject_error_middleware(crawler, engine)
    else:
        try:
            _inject_error_middleware(crawler, crawler.engine)
        except (AttributeError, RuntimeError):
            pass


def enable_ingest(crawler):
    """
    Idempotently enable request logging, error logging, parent_url tracking,
    job logs, and stats. Called from DbInsertPipeline so projects only
    need ITEM_PIPELINES.
    """
    if getattr(crawler, "_ingest_enabled", False):
        return
    crawler._ingest_enabled = True

    ensure_collector(crawler)
    update_available()

    LoggingExtension.from_crawler(crawler)
    StatsExtension.from_crawler(crawler)
    RequestLogger.from_crawler(crawler)

    attach_runtime_hooks(crawler)
