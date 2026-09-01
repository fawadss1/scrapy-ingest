"""
Database schema management utilities for scrapy_ingest.
"""
import logging

logger = logging.getLogger(__name__)

_VARCHAR_TYPES = ("character varying", "varchar", "text")


class SchemaManager:
    """Database schema management"""

    def __init__(self, db_connection, settings):
        self.db = db_connection
        self.settings = settings

    def create_jobs_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_jobs_table} (
            id SERIAL PRIMARY KEY,
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
            stats JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(sql)
        logger.info("Jobs table %s created/verified", self.settings.db_jobs_table)

    def create_items_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_items_table} (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES {self.settings.db_jobs_table}(id) ON DELETE CASCADE,
            item JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(sql)
        logger.info("Items table %s created/verified", self.settings.db_items_table)

    def create_requests_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_requests_table} (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES {self.settings.db_jobs_table}(id) ON DELETE CASCADE,
            url TEXT,
            method VARCHAR(10),
            status_code INTEGER,
            response_time FLOAT,
            fingerprint VARCHAR(64),
            parent_id INTEGER,
            parent_url TEXT,
            error TEXT,
            success BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES {self.settings.db_requests_table}(id)
        )
        """
        self.db.execute(sql)
        logger.info("Requests table %s created/verified", self.settings.db_requests_table)

    def create_logs_table(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.settings.db_logs_table} (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES {self.settings.db_jobs_table}(id) ON DELETE CASCADE,
            time VARCHAR(32),
            level VARCHAR(50),
            logger VARCHAR(255),
            message TEXT,
            exception TEXT
        )
        """
        self.db.execute(sql)
        logger.info("Logs table %s created/verified", self.settings.db_logs_table)

    def _has_row(self, sql, params):
        return self.db.execute(sql, params) is not None

    def _table_exists(self, table):
        return self._has_row(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s AND table_schema = current_schema()
            """,
            (table.lower(),),
        )

    def _rename_legacy_jobs_table(self):
        """Rename leftover job_details table to jobs when using the default name."""
        target = self.settings.db_jobs_table
        if target != "jobs":
            return
        if self._table_exists("jobs") or not self._table_exists("job_details"):
            return
        self.db.execute("ALTER TABLE job_details RENAME TO jobs")
        logger.info("Renamed table job_details to jobs")

    def _column_exists(self, table, column):
        return self._has_row(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table.lower(), column.lower()),
        )

    def _column_type(self, table, column):
        row = self.db.execute(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table.lower(), column.lower()),
        )
        return row[0] if row else None

    def _ensure_column(self, table, column, coltype):
        if self._column_exists(table, column):
            return
        self.db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
        logger.info("Added column %s.%s", table, column)

    def _constraint_exists(self, table, constraint_name):
        return self._has_row(
            """
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name = %s AND constraint_name = %s
            """,
            (table.lower(), constraint_name.lower()),
        )

    def _child_tables(self):
        return (
            self.settings.db_items_table,
            self.settings.db_requests_table,
            self.settings.db_logs_table,
        )

    def _backfill_job_details(self):
        """Create jobs rows for leftover string job_id values."""
        varchar_tables = [
            table
            for table in self._child_tables()
            if self._column_type(table, "job_id") in _VARCHAR_TYPES
        ]
        if not varchar_tables:
            return

        details = self.settings.db_jobs_table
        union = " UNION ".join(
            f"SELECT job_id FROM {table} WHERE job_id IS NOT NULL" for table in varchar_tables
        )
        sql = f"""
        INSERT INTO {details} (job_id, status)
        SELECT DISTINCT src.job_id, 'imported'
        FROM ({union}) src
        WHERE NOT EXISTS (
            SELECT 1 FROM {details} d WHERE d.job_id = src.job_id
        )
        """
        self.db.execute(sql)

    def _ensure_job_id_fk(self, child_table):
        constraint = f"{child_table}_job_id_fkey"
        if self._constraint_exists(child_table, constraint):
            return
        self.db.execute(
            f"""
            ALTER TABLE {child_table}
            ADD CONSTRAINT {constraint}
            FOREIGN KEY (job_id) REFERENCES {self.settings.db_jobs_table}(id)
            ON DELETE CASCADE
            """
        )
        logger.info(
            "Added FK %s.job_id -> %s.id",
            child_table,
            self.settings.db_jobs_table,
        )

    def _convert_child_job_id_to_pk(self, child_table):
        """Turn leftover VARCHAR job_id values into jobs.id integers."""
        data_type = self._column_type(child_table, "job_id")
        if data_type in ("integer", "bigint"):
            self._ensure_job_id_fk(child_table)
            return
        if data_type not in _VARCHAR_TYPES:
            return

        details = self.settings.db_jobs_table
        constraint = f"{child_table}_job_id_fkey"
        if self._constraint_exists(child_table, constraint):
            self.db.execute(f"ALTER TABLE {child_table} DROP CONSTRAINT {constraint}")

        self.db.execute(f"ALTER TABLE {child_table} ADD COLUMN job_id_pk INTEGER")
        self.db.execute(
            f"""
            UPDATE {child_table} AS child
            SET job_id_pk = details.id
            FROM {details} AS details
            WHERE details.job_id = child.job_id
            """
        )
        self.db.execute(f"ALTER TABLE {child_table} DROP COLUMN job_id")
        self.db.execute(f"ALTER TABLE {child_table} RENAME COLUMN job_id_pk TO job_id")
        self._ensure_job_id_fk(child_table)
        logger.info("Converted %s.job_id to jobs.id", child_table)

    def migrate_columns(self):
        """Add columns introduced after the original schema."""
        for name, coltype in (
            ("error", "TEXT"),
            ("success", "BOOLEAN"),
        ):
            self._ensure_column(self.settings.db_requests_table, name, coltype)

        for name, coltype in (
            ("time", "VARCHAR(32)"),
            ("logger", "VARCHAR(255)"),
            ("exception", "TEXT"),
        ):
            self._ensure_column(self.settings.db_logs_table, name, coltype)

        for name, coltype in (
            ("elapsed_seconds", "FLOAT DEFAULT 0"),
            ("items_per_min", "FLOAT DEFAULT 0"),
        ):
            self._ensure_column(self.settings.db_jobs_table, name, coltype)

        self._backfill_job_details()
        for table in self._child_tables():
            self._convert_child_job_id_to_pk(table)

    def ensure_tables_exist(self):
        if not self.settings.create_tables:
            logger.info("Table creation disabled. Skipping table creation.")
            return

        try:
            self._rename_legacy_jobs_table()
            self.create_jobs_table()
            self.create_items_table()
            self.create_requests_table()
            self.create_logs_table()
            self.migrate_columns()
            self.db.commit()
            logger.info("All tables created/verified successfully")
        except Exception as e:
            logger.error("Failed to create tables: %s", e)
            self.db.rollback()
            raise
