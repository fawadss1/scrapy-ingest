from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from scrapy_ingest.config.settings import Settings, validate_settings
from scrapy_ingest.database.search import SearchClient, SearchWriter


def _settings(**values):
    crawler_settings = MagicMock()
    crawler_settings.get.side_effect = lambda key, default=None: values.get(key, default)
    crawler_settings.getbool.side_effect = lambda key, default=False: values.get(
        key, default
    )
    return Settings(crawler_settings)


class TestIngestDestinations:
    def test_defaults_to_database_only(self):
        settings = _settings(DB_URL="postgresql://localhost/db")
        assert settings.ingest_to_database is True
        assert settings.ingest_to_search is False

    def test_search_only_skips_database_validation(self):
        settings = _settings(
            INGEST_TO_DATABASE=False,
            INGEST_TO_SEARCH=True,
            SEARCH_URL="http://localhost:9200",
        )
        assert validate_settings(settings) is True

    def test_search_requires_url(self):
        settings = _settings(INGEST_TO_DATABASE=False, INGEST_TO_SEARCH=True)
        with pytest.raises(ValueError, match="SEARCH_URL is required"):
            validate_settings(settings)

    def test_requires_at_least_one_destination(self):
        settings = _settings(INGEST_TO_DATABASE=False, INGEST_TO_SEARCH=False)
        with pytest.raises(ValueError, match="at least one destination"):
            validate_settings(settings)


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
