"""
Base extension functionality for scrapy_item_ingest.
"""
import logging

from scrapy_item_ingest.config.settings import Settings, validate_settings
from ..utils.time import get_current_datetime
from ..database.connection import DatabaseConnection
from ..database.schema import SchemaManager

logger = logging.getLogger(__name__)


class BaseExtension:
    """Base extension with common functionality"""

    def __init__(self, settings):
        self.settings = settings
        validate_settings(settings)
        # Lazy-initialized shared DB connection and schema manager
        self._db = None
        self._schema_manager = None
        # Prevent repeated error spam if DB logging fails
        self._db_logging_enabled = True

    @classmethod
    def from_crawler(cls, crawler):
        """Create extension instance from crawler"""
        settings = Settings(crawler.settings)
        return cls(settings)

    def get_identifier_info(self, spider):
        """Get identifier column and value for the spider"""
        return self.settings.get_identifier_column(), self.settings.get_identifier_value(spider)

    def _ensure_db_initialized(self):
        """Initialize DB connection and schema manager lazily."""
        if self._db is None:
            self._db = DatabaseConnection(self.settings.db_url)
            if not self._db.connect():
                raise RuntimeError("Failed to connect to database for logging")
        if self._schema_manager is None:
            self._schema_manager = SchemaManager(self._db, self.settings)

    def _ensure_logs_table_exists(self):
        """Create logs table if it doesn't exist (only if create_tables is True)."""
        if not self.settings.create_tables:
            return
        try:
            self._schema_manager.create_logs_table()
            self._db.commit()
        except Exception as e:
            self._db.rollback()

    def _log_to_database(self, spider, log_level, message):
        """Helper method to log messages to database using shared DBConnection."""
        if not self._db_logging_enabled:
            return
        try:
            self._ensure_db_initialized()
            self._ensure_logs_table_exists()

            identifier_column, identifier_value = self.get_identifier_info(spider)
            sql = f"""
                INSERT INTO {self.settings.db_logs_table}
                ({identifier_column}, level, message, time)
                VALUES (%s, %s, %s, %s)
            """
            self._db.execute(
                sql,
                (
                    identifier_value,
                    log_level,
                    message,
                    get_current_datetime(self.settings).strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            self._db.commit()
        except Exception as e:
            # Disable further DB logging to avoid spamming errors
            self._db_logging_enabled = False
