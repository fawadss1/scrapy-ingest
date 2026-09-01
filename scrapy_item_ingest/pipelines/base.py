"""
Base pipeline functionality for scrapy_item_ingest.
"""
from ..config.settings import Settings, validate_settings


class BasePipeline:
    """Base pipeline with settings validation."""

    def __init__(self, settings):
        self.settings = settings
        validate_settings(settings)

    @classmethod
    def from_crawler(cls, crawler):
        settings = Settings(crawler.settings)
        return cls(settings)

    def get_identifier_info(self, spider):
        return self.settings.get_identifier_column(), self.settings.get_identifier_value(spider)
