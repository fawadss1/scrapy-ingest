from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from scrapy_ingest.config.settings import Settings, validate_settings
from scrapy_ingest.exceptions import ConfigurationError, IngestConnectionError
from scrapy_ingest.database.search import SearchClient, SearchWriter


def _settings(**values):
    crawler_settings = MagicMock()
    crawler_settings.get.side_effect = lambda key, default=None: values.get(key, default)
    crawler_settings.getbool.side_effect = lambda key, default=False: values.get(
        key, default
    )
    return Settings(crawler_settings)


class TestIngestDestinations:
    def test_database_only_from_db_url(self):
        settings = _settings(DB_URL="postgresql://localhost/db")
        assert settings.ingest_to_database is True
        assert settings.ingest_to_search is False
        assert validate_settings(settings) is True

    def test_search_only_from_search_url(self):
        settings = _settings(SEARCH_URL="http://localhost:9200")
        assert settings.ingest_to_database is False
        assert settings.ingest_to_search is True
        assert validate_settings(settings) is True

    def test_both_when_db_and_search_are_configured(self):
        settings = _settings(
            DB_URL="postgresql://localhost/db",
            SEARCH_URL="http://localhost:9200",
        )
        assert settings.ingest_to_database is True
        assert settings.ingest_to_search is True
        assert validate_settings(settings) is True

    def test_requires_at_least_one_destination(self):
        settings = _settings()
        with pytest.raises(ConfigurationError, match="Configure at least one destination"):
            validate_settings(settings)

    def test_database_from_discrete_fields(self):
        settings = _settings(
            DB_HOST="localhost",
            DB_USER="u",
            DB_PASSWORD="p",
            DB_NAME="db",
        )
        assert settings.ingest_to_database is True
        assert validate_settings(settings) is True


class TestSearchWriter:
    def test_bulk_indexes_batch(self):
        settings = _settings(
            SEARCH_URL="http://localhost:9200",
            SEARCH_INDEX_PREFIX="ingest",
        )
        client = MagicMock()
        writer = SearchWriter(client, settings)
        writer._started_at = datetime.now(timezone.utc)
        writer.write(
            {
                "items": [{"title": "one"}],
                "requests": [{"url": "https://example.com", "success": True}],
                "logs": [{"level": "INFO", "message": "ok"}],
            },
            "job-1",
        )
        assert client.bulk.call_count == 3
        assert writer._counts["items_count"] == 1
        assert writer._counts["requests_count"] == 1
        assert writer._counts["logs_count"] == 1


class TestSearchClient:
    def test_connects_with_auth_and_bulk(self):
        settings = _settings(
            SEARCH_URL="https://localhost:9200",
            SEARCH_USER="elastic",
            SEARCH_PASSWORD="secret",
        )
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.indices.exists.return_value = True

        with (
            patch("scrapy_ingest.database.search.OpenSearch", return_value=mock_client) as mock_os,
            patch("scrapy_ingest.database.search.os_bulk", return_value=(1, [])) as mock_bulk,
        ):
            client = SearchClient(settings)
            client.ping()
            client.bulk("ingest-job_items", [{"job_id": "job-1", "item": {"a": 1}}])

        mock_os.assert_called_once()
        kwargs = mock_os.call_args.kwargs
        assert kwargs["hosts"] == ["https://localhost:9200"]
        assert kwargs["http_auth"] == ("elastic", "secret")
        assert kwargs["use_ssl"] is True
        mock_bulk.assert_called_once()

    def test_ping_failure_raises_connection_error(self):
        settings = _settings(SEARCH_URL="http://localhost:9200")
        mock_client = MagicMock()
        mock_client.ping.return_value = False

        with patch("scrapy_ingest.database.search.OpenSearch", return_value=mock_client):
            client = SearchClient(settings)
            with pytest.raises(IngestConnectionError, match="did not respond to ping"):
                client.ping()
