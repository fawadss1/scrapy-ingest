"""
Database schema management utilities for scrapy_ingest.
"""
import logging

logger = logging.getLogger(__name__)


class SchemaManager:
    """Create ingest tables if they do not already exist."""

    def __init__(self, db_connection, settings):
        self.db = db_connection
        self.settings = settings
        mysql = getattr(settings, "db_dialect", "postgres") == "mysql"
        self._pk = (
            "INT NOT NULL AUTO_INCREMENT PRIMARY KEY" if mysql else "SERIAL PRIMARY KEY"
        )
        self._json = "JSON" if mysql else "JSONB"
        self._bool = "BOOLEAN"
        self._suffix = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" if mysql else ""
        self._time = "`time`" if mysql else "time"

    def create_jobs_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_jobs_table} (
            id {self._pk},
            job_id VARCHAR(255) UNIQUE NOT NULL,
            spider_name VARCHAR(255),
            status VARCHAR(32),
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            finish_reason VARCHAR(255),
            requests_count INTEGER DEFAULT 0,
            success_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            items_count INTEGER DEFAULT 0,
            logs_count INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            items_per_min FLOAT DEFAULT 0,
            elapsed_seconds FLOAT DEFAULT 0,
            stats {self._json},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ){self._suffix}
        """
        self.db.execute(sql)
        logger.info("Jobs table %s created/verified", self.settings.db_jobs_table)

    def create_items_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_items_table} (
            id {self._pk},
            job_id INTEGER,
            item {self._json},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES {self.settings.db_jobs_table}(id) ON DELETE CASCADE
        ){self._suffix}
        """
        self.db.execute(sql)
        logger.info("Items table %s created/verified", self.settings.db_items_table)

    def create_requests_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_requests_table} (
            id {self._pk},
            job_id INTEGER,
            url TEXT,
            method VARCHAR(10),
            status_code INTEGER,
            response_time FLOAT,
            fingerprint VARCHAR(64),
            parent_id INTEGER,
            parent_url TEXT,
            error TEXT,
            success {self._bool},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES {self.settings.db_jobs_table}(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES {self.settings.db_requests_table}(id)
        ){self._suffix}
        """
        self.db.execute(sql)
        logger.info("Requests table %s created/verified", self.settings.db_requests_table)

    def create_logs_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_logs_table} (
            id {self._pk},
            job_id INTEGER,
            {self._time} VARCHAR(32),
            level VARCHAR(50),
            logger VARCHAR(255),
            message TEXT,
            exception TEXT,
            FOREIGN KEY (job_id) REFERENCES {self.settings.db_jobs_table}(id) ON DELETE CASCADE
        ){self._suffix}
        """
        self.db.execute(sql)
        logger.info("Logs table %s created/verified", self.settings.db_logs_table)

    def ensure_tables_exist(self):
        if not self.settings.create_tables:
            logger.info("Table creation disabled. Skipping table creation.")
            return

        try:
            self.create_jobs_table()
            self.create_items_table()
            self.create_requests_table()
            self.create_logs_table()
            self.db.commit()
            logger.info("All tables created/verified successfully")
        except Exception as e:
            logger.error("Failed to create tables: %s", e)
            self.db.rollback()
            raise
