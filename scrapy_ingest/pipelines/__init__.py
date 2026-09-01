"""Pipeline modules for scrapy_ingest."""

from .items import ItemsPipeline
from .main import DbInsertPipeline
from .requests import RequestsPipeline

__all__ = [
    "DbInsertPipeline",
    "ItemsPipeline",
    "RequestsPipeline",
]
