import pytest
from unittest.mock import MagicMock

from scrapy_ingest.config.settings import Settings, validate_settings
from scrapy_ingest.exceptions import (
    ConfigurationError,
    DatabaseError,
    DependencyError,
    FlushError,
    IngestConnectionError,
    IngestError,
    SchemaError,
    SearchError,
)


def _settings(**values):
    crawler_settings = MagicMock()
    crawler_settings.get.side_effect = lambda key, default=None: values.get(key, default)
    crawler_settings.getbool.side_effect = lambda key, default=False: values.get(
        key, default
    )
    return Settings(crawler_settings)


class TestExceptionHierarchy:
    def test_base_subclasses(self):
        for cls in (
            ConfigurationError,
            DependencyError,
            IngestConnectionError,
            DatabaseError,
            SchemaError,
            SearchError,
            FlushError,
        ):
            assert issubclass(cls, IngestError)
            assert issubclass(cls, Exception)

    def test_schema_is_database_error(self):
        assert issubclass(SchemaError, DatabaseError)

    def test_configuration_error_from_validate_settings(self):
        settings = _settings()
        with pytest.raises(ConfigurationError, match="Configure at least one destination"):
            validate_settings(settings)

    def test_connection_error_is_not_builtin(self):
        assert IngestConnectionError is not ConnectionError


class TestPublicExports:
    def test_import_from_package(self):
        import scrapy_ingest as ingest

        assert ingest.ConfigurationError is ConfigurationError
        assert ingest.IngestError is IngestError
        assert ingest.FlushError is FlushError
