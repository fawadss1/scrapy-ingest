"""Items pipeline for collecting scraped items."""
import time

from itemadapter import ItemAdapter

from .base import BasePipeline
from ..collector import ensure_collector
from ..config.settings import Settings
from ..database.flusher import get_flusher
from ..utils.updates import update_available


class ItemsPipeline(BasePipeline):
    """Collect items into the shared buffer and flush them to PostgreSQL."""

    def __init__(self, settings, crawler=None):
        super().__init__(settings)
        self.crawler = crawler
        self.collector = ensure_collector(crawler) if crawler is not None else None

    @classmethod
    def from_crawler(cls, crawler):
        ensure_collector(crawler)
        update_available()
        settings = Settings(crawler.settings)
        return cls(settings, crawler)

    def open_spider(self, spider):
        self.collector = ensure_collector(self.crawler)
        get_flusher(self.crawler, self.settings).start(spider)

    def close_spider(self, spider):
        get_flusher(self.crawler, self.settings).stop_periodic()

    def process_item(self, item, spider):
        data = ItemAdapter(item).asdict()
        data["crawled_at"] = int(time.time())
        self.collector.add_item(data)
        if self.collector.size() >= self.settings.ingest_batch_size:
            get_flusher(self.crawler, self.settings).flush(spider)
        return item
