"""Main pipeline that auto-enables items, requests, logs, and stats."""
from .items import ItemsPipeline
from ..bootstrap import enable_ingest
from ..config.settings import Settings


class IngestPipeline(ItemsPipeline):
    """
    Collect items and flush unified batches to configured destinations.

    Writes to PostgreSQL/MySQL (``DB_URL``), Elasticsearch/OpenSearch
    (``SEARCH_URL``), or both. Enabling this pipeline also auto-enables
    request logging, error logging, parent_url tracking, job logs, and stats —
    no EXTENSIONS or extra DOWNLOADER_MIDDLEWARES required.
    """

    @classmethod
    def from_crawler(cls, crawler):
        enable_ingest(crawler)
        settings = Settings(crawler.settings)
        return cls(settings, crawler)