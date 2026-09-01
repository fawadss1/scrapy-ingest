"""Standalone pipeline that enables request tracking and flushes to PostgreSQL."""
from .base import BasePipeline
from ..bootstrap import attach_runtime_hooks
from ..collector import ensure_collector
from ..config.settings import Settings
from ..database.flusher import get_flusher
from ..extensions.request_logger import RequestLogger
from ..utils.updates import update_available


class RequestsPipeline(BasePipeline):
    """
    Enable request logging (success + errors + parent_url) without items/logs.

    Prefer DbInsertPipeline, which turns this on automatically.
    """

    def __init__(self, settings, crawler=None):
        super().__init__(settings)
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        ensure_collector(crawler)
        update_available()
        RequestLogger.from_crawler(crawler)
        attach_runtime_hooks(crawler)
        settings = Settings(crawler.settings)
        return cls(settings, crawler)

    def open_spider(self, spider):
        get_flusher(self.crawler, self.settings).start(spider)

    def close_spider(self, spider):
        get_flusher(self.crawler, self.settings).stop_periodic()

    def process_item(self, item, spider):
        return item
