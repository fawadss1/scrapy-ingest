"""
scrapy_ingest - A Scrapy extension for ingesting items, requests, logs, and stats into PostgreSQL.

Enabling DbInsertPipeline auto-enables request logging (with parent_url),
error logging, full job logs (including print()), and crawl stats.
"""

from .extensions.log_handler import install_early

install_early()

__version__ = "1.0.0"
__author__ = "Fawad Ali"
__description__ = "Scrapy extension for database ingestion with job/spider tracking"

from .pipelines.main import DbInsertPipeline
from .extensions.logging import LoggingExtension
from .extensions.stats import StatsExtension
from .pipelines.items import ItemsPipeline
from .pipelines.requests import RequestsPipeline
from .extensions.request_logger import RequestLogger
from .config.settings import Settings, validate_settings

__all__ = [
    "DbInsertPipeline",
    "LoggingExtension",
    "StatsExtension",
    "ItemsPipeline",
    "RequestsPipeline",
    "RequestLogger",
    "Settings",
    "validate_settings",
    "__version__",
    "__author__",
    "__description__",
]
