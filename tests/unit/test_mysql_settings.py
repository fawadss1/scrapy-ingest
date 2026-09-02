from unittest.mock import MagicMock

import pytest

from scrapy_ingest.config.settings import Settings, validate_settings
from scrapy_ingest.database.writer import DbWriter


def _settings(**values):
    crawler_settings = MagicMock()
    crawler_settings.get.side_effect = lambda key, default=None: values.get(key, default)
    crawler_settings.getbool.side_effect = lambda key, default=False: values.get(
        key, default
    )
    return Settings(crawler_settings)


class TestDialectDetection:
    def test_postgres_url(self):
        settings = _settings(DB_URL="postgresql://u:p@localhost:5432/db")
        assert settings.db_dialect == "postgres"

    def test_mysql_url(self):
        settings = _settings(DB_URL="mysql://u:p@localhost:3306/db")
        assert settings.db_dialect == "mysql"

    def test_mysql_from_db_type(self):
        settings = _settings(DB_TYPE="mysql", DB_HOST="localhost", DB_NAME="db")
        assert settings.db_dialect == "mysql"
        assert settings.db_url.startswith("mysql://")
        assert ":3306/" in settings.db_url

    def test_mariadb_alias(self):
        settings = _settings(DB_TYPE="mariadb", DB_HOST="dbhost", DB_NAME="app")
        assert settings.db_dialect == "mysql"
        assert settings.db_url.startswith("mysql://")


class TestValidateSettings:
    def test_accepts_mysql_url(self):
        settings = _settings(DB_URL="mysql://u:p@localhost:3306/db")
        assert validate_settings(settings) is True

    def test_accepts_mysql_discrete_fields(self):
        settings = _settings(
            DB_TYPE="mysql",
            DB_HOST="localhost",
            DB_USER="u",
            DB_PASSWORD="p",
            DB_NAME="db",
        )
        assert validate_settings(settings) is True

    def test_rejects_unknown_url_scheme(self):
        settings = _settings(DB_URL="oracle://u:p@localhost/db")
        with pytest.raises(ValueError, match="Unsupported database URL scheme"):
            validate_settings(settings)


class TestWriterSql:
    def test_postgres_upsert_returns_id(self):
        writer = DbWriter(MagicMock(), _settings(DB_URL="postgresql://localhost/db"))
        sql = writer._upsert_job_sql("jobs")
        assert "ON CONFLICT" in sql
        assert "RETURNING id" in sql
        assert writer._is_mysql() is False

    def test_mysql_upsert_uses_duplicate_key(self):
        writer = DbWriter(MagicMock(), _settings(DB_URL="mysql://localhost/db"))
        sql = writer._upsert_job_sql("jobs")
        assert "ON DUPLICATE KEY UPDATE" in sql
        assert "RETURNING" not in sql
        assert writer._is_mysql() is True

    def test_mysql_link_parent_uses_join(self):
        writer = DbWriter(MagicMock(), _settings(DB_URL="mysql://localhost/db"))
        sql = writer._link_parent_sql("job_requests")
        assert "INNER JOIN" in sql
        assert "SET child.parent_id" in sql
        assert "FROM job_requests AS parent" not in sql

    def test_postgres_link_parent_uses_subquery(self):
        writer = DbWriter(MagicMock(), _settings(DB_URL="postgresql://localhost/db"))
        sql = writer._link_parent_sql("job_requests")
        assert "SET parent_id" in sql
        assert "FROM job_requests AS parent" in sql
