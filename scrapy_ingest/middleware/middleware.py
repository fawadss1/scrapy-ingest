import logging
import re
import time
from functools import wraps

from scrapy import Request, signals
from scrapy.utils.asyncgen import as_async_generator

from ..utils.fingerprint import get_request_fingerprint
from ..utils.parent import get_parent_url, set_parent_url

logger = logging.getLogger(__name__)


def _stamp_parent_url(output, response, crawler):
    """Attach crawl-graph parent (response URL) onto a yielded Request."""
    if not isinstance(output, Request):
        return output
    parent = getattr(response, "url", None)
    if not parent:
        return output
    set_parent_url(output, parent, crawler)
    return output


def _inject_into_scraper(crawler, scraper):
    """Patch scraper methods so yielded Requests get parent_url."""
    if getattr(crawler, "_ingest_parent_url_hooked", False):
        return
    if scraper is None:
        return

    hooked = False

    if hasattr(scraper, "handle_spider_output_async"):
        original_handle = scraper.handle_spider_output_async

        @wraps(original_handle)
        async def _wrapped_handle(result, request, response):
            async def _stamped():
                async for o in as_async_generator(result):
                    _stamp_parent_url(o, response, crawler)
                    yield o

            return await original_handle(_stamped(), request, response)

        scraper.handle_spider_output_async = _wrapped_handle
        hooked = True

    if hasattr(scraper, "_process_spidermw_output_async"):
        original_async = scraper._process_spidermw_output_async

        @wraps(original_async)
        async def _wrapped_async(output, response):
            _stamp_parent_url(output, response, crawler)
            return await original_async(output, response)

        scraper._process_spidermw_output_async = _wrapped_async
        hooked = True

    spidermw = getattr(scraper, "spidermw", None)
    if spidermw is not None and hasattr(spidermw, "_process_callback_output"):
        original_cb = spidermw._process_callback_output

        @wraps(original_cb)
        async def _wrapped_cb(response, result):
            async def _stamped():
                async for o in result:
                    _stamp_parent_url(o, response, crawler)
                    yield o

            return await original_cb(response, _stamped())

        spidermw._process_callback_output = _wrapped_cb
        hooked = True

    if hooked:
        crawler._ingest_parent_url_hooked = True
        logger.debug("parent_url tracking enabled")
    else:
        logger.warning("parent_url tracking: no scraper hooks found")


def install_parent_url_tracking(crawler):
    """
    Package-level parent URL tracking (no spider settings needed).

    If the engine already exists (pipeline bootstrap), inject immediately.
    Otherwise patch engine creation. Safe to call multiple times.
    """
    if not hasattr(crawler, "ingest_parent_by_fp"):
        crawler.ingest_parent_by_fp = {}

    if getattr(crawler, "_ingest_parent_url_hooked", False):
        return

    if getattr(crawler, "_ingest_parent_url_tracking", False):
        try:
            _inject_into_scraper(crawler, crawler.engine.scraper)
        except (AttributeError, RuntimeError):
            pass
        return

    crawler._ingest_parent_url_tracking = True

    try:
        scraper = crawler.engine.scraper
    except (AttributeError, RuntimeError):
        scraper = None

    if scraper is not None:
        _inject_into_scraper(crawler, scraper)
        crawler.signals.connect(
            lambda spider=None: crawler.ingest_parent_by_fp.clear(),
            signal=signals.spider_closed,
        )
        return

    if not getattr(crawler, "_ingest_create_engine_patched", False):
        original_create_engine = crawler._create_engine

        def _create_engine_and_hook():
            engine = original_create_engine()
            _inject_into_scraper(crawler, getattr(engine, "scraper", None))
            return engine

        crawler._create_engine = _create_engine_and_hook
        crawler._ingest_create_engine_patched = True

    def _clear(spider=None):
        crawler.ingest_parent_by_fp.clear()

    crawler.signals.connect(_clear, signal=signals.spider_closed)


class ErrorMiddleware:
    """
    Downloader middleware that logs request errors/exceptions.

    Works with RequestLogger, which handles successful responses.
    """

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        middleware.crawler = crawler

        from ..collector import ensure_collector

        middleware.collector = ensure_collector(crawler)
        install_parent_url_tracking(crawler)
        return middleware

    def process_exception(self, request, exception, spider):
        start_time = request.meta.get("start_time", time.time())
        elapsed_seconds = time.time() - start_time
        status_code = self._extract_status_code(exception)

        self.collector.add_request(
            {
                "url": request.url,
                "parent_url": get_parent_url(request, getattr(self, "crawler", None)),
                "method": request.method,
                "status_code": status_code,
                "response_time_secs": round(elapsed_seconds, 2),
                "fingerprint": get_request_fingerprint(request),
                "error": f"{exception.__class__.__name__}: {str(exception)}",
                "success": False,
            }
        )
        return None

    def _extract_status_code(self, exception):
        status_match = re.search(r"\[(\d{3})]", str(exception))
        if status_match:
            return int(status_match.group(1))

        if hasattr(exception, "status"):
            return exception.status

        if hasattr(exception, "response") and hasattr(exception.response, "status"):
            return exception.response.status

        return 0
