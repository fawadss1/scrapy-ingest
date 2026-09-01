import time

from scrapy import signals

from ..collector import ensure_collector
from ..middleware import install_parent_url_tracking
from ..utils.fingerprint import get_request_fingerprint
from ..utils.parent import get_parent_url


class RequestLogger:
    """Log successful HTTP responses into the shared collector."""

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
                "response_time": round(time.time() - start, 2),
                "fingerprint": get_request_fingerprint(request),
                "error": None,
                "success": 200 <= response.status < 300,
            }
        )
