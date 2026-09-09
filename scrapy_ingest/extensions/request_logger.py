import time

from scrapy import signals

from ..collector import ensure_collector
from ..middleware import install_parent_url_tracking
from ..utils.fingerprint import get_request_fingerprint
from ..utils.parent import get_parent_url


def _format_spider_error(failure):
    exc = failure.value
    name = failure.type.__name__ if failure.type else type(exc).__name__
    tb = failure.getTraceback()
    if tb:
        return f"{name}: {exc}\n{tb}".rstrip()
    return f"{name}: {exc}"


def _request_from_spider_error(failure, response):
    request = getattr(response, "request", None)
    if request is not None:
        return request
    request = getattr(failure, "request", None)
    if request is not None:
        return request
    value = getattr(failure, "value", None)
    return getattr(value, "request", None)


class RequestLogger:
    """Log HTTP responses and spider callback errors into the shared collector."""

    @classmethod
    def from_crawler(cls, crawler):
        if getattr(crawler, "_ingest_request_logger", None) is not None:
            return crawler._ingest_request_logger

        ext = cls()
        ext.crawler = crawler
        ext.collector = ensure_collector(crawler)
        install_parent_url_tracking(crawler)

        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        crawler._ingest_request_logger = ext
        return ext

    def request_scheduled(self, request, spider):
        request.meta["start_time"] = time.time()

    def response_received(self, response, request, spider):
        start = request.meta.get("start_time", time.time())
        self.collector.add_request(
            {
                "url": request.url,
                "parent_url": get_parent_url(request, self.crawler),
                "method": request.method,
                "status_code": response.status,
                "response_time_secs": round(time.time() - start, 2),
                "fingerprint": get_request_fingerprint(request),
                "error": None,
                "success": 200 <= response.status < 300,
            }
        )

    def spider_error(self, failure, response, spider):
        request = _request_from_spider_error(failure, response)
        if request is None:
            return

        fingerprint = get_request_fingerprint(request)
        error = _format_spider_error(failure)
        if self.collector.mark_request_error(fingerprint, error):
            return

        start = request.meta.get("start_time", time.time())
        status_code = getattr(response, "status", 0)
        self.collector.add_request(
            {
                "url": request.url,
                "parent_url": get_parent_url(request, self.crawler),
                "method": request.method,
                "status_code": status_code,
                "response_time_secs": round(time.time() - start, 2),
                "fingerprint": fingerprint,
                "error": error,
                "success": False,
            }
        )
