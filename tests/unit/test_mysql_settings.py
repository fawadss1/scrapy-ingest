from unittest.mock import MagicMock

import pytest

from scrapy_ingest.config.settings import Settings, validate_settings
from scrapy_ingest.database.dialect import (
    MysqlDialect,
    PostgresDialect,
    dialect_from_url,
    get_dialect,
)


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
        assert dialect_from_url(settings.db_url) == "postgres"

    def test_mysql_url(self):
        settings = _settings(DB_URL="mysql://u:p@localhost:3306/db")
        assert settings.db_dialect == "mysql"
        assert dialect_from_url(settings.db_url) == "mysql"

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


class TestDialectSql:
    def test_postgres_upsert_returns_id(self):
        dialect = PostgresDialect()
        sql = dialect.upsert_job_sql("jobs")
        assert "ON CONFLICT" in sql
        assert "RETURNING id" in sql
        assert dialect.upsert_returns_id() is True

    def test_mysql_upsert_uses_duplicate_key(self):
        dialect = MysqlDialect()
        sql = dialect.upsert_job_sql("jobs")
        assert "ON DUPLICATE KEY UPDATE" in sql
        assert "RETURNING" not in sql
        assert dialect.upsert_returns_id() is False
        assert dialect.json_type == "JSON"
        assert "AUTO_INCREMENT" in dialect.serial_pk

    def test_get_dialect_from_settings(self):
        assert isinstance(
            get_dialect(_settings(DB_URL="mysql://localhost/db")), MysqlDialect
        )
        assert isinstance(
            get_dialect(_settings(DB_URL="postgresql://localhost/db")), PostgresDialect
        )
