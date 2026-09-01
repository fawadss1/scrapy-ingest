import logging

from scrapy import signals

from ..collector import ensure_collector
from ..utils.serialization import json_safe
from ..utils.updates import update_available

logger = logging.getLogger(__name__)


class StatsExtension:
    """Copy Scrapy crawl stats into the shared collector when the spider closes."""

    @classmethod
    def from_crawler(cls, crawler):
        if getattr(crawler, "_ingest_stats_ext", None) is not None:
            return crawler._ingest_stats_ext

        update_available()
        ext = cls()
        ext.collector = ensure_collector(crawler)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler._ingest_stats_ext = ext
        return ext

    def spider_closed(self, spider, reason):
        spider.crawler.ingest_finish_reason = reason
        try:
            stats = spider.crawler.stats.get_stats()
            self.collector.set_stats(json_safe(stats))
        except Exception:
            logger.exception("Failed to collect stats")
