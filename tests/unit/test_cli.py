from unittest.mock import MagicMock, patch

import pytest

from scrapy_ingest.cli import (
    _run_spinner,
    _truncate,
    check_config_command,
    run_check_config,
)


def _settings(**values):
    crawler_settings = MagicMock()
    crawler_settings.get.side_effect = lambda key, default=None: values.get(key, default)
    crawler_settings.getbool.side_effect = lambda key, default=False: values.get(
        key, default
    )
    crawler_settings.set = MagicMock()
    return crawler_settings


class TestTruncate:
    def test_shortens_long_error_messages(self):
        text = "x" * 100
        assert len(_truncate(text)) == 72
        assert _truncate(text).endswith("...")


class TestRunCheckConfig:
    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_database_only_success(self, load_settings):
        load_settings.return_value = _settings(
            DB_URL="postgresql://localhost:5432/scrapy_data"
        )
        with patch("scrapy_ingest.database.connection.DatabaseConnection") as db_cls:
            db_cls.return_value.close = MagicMock()
            ok, rows = run_check_config(use_spinner=False)
        assert ok is True
        assert any(row[1] == "database" and row[2] == "OK" for row in rows)

    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_search_only_success(self, load_settings):
        load_settings.return_value = _settings(SEARCH_URL="http://localhost:9200")
        with patch("scrapy_ingest.database.search.SearchClient") as search_cls:
            client = search_cls.return_value
            ok, rows = run_check_config(use_spinner=False)
        assert ok is True
        client.ping.assert_called_once()
        client.close.assert_called_once()
        assert any(row[1] == "search" and row[2] == "OK" for row in rows)

    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_no_destination_fails(self, load_settings):
        load_settings.return_value = _settings()
        ok, rows = run_check_config(use_spinner=False)
        assert ok is False
        assert rows[0][2] == "FAIL"

    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_database_ping_failure(self, load_settings):
        from scrapy_ingest.exceptions import IngestConnectionError

        load_settings.return_value = _settings(
            DB_URL="postgresql://localhost:5432/scrapy_data"
        )
        with patch(
            "scrapy_ingest.database.connection.DatabaseConnection",
            side_effect=IngestConnectionError("connection refused"),
        ):
            ok, rows = run_check_config(use_spinner=False)
        assert ok is False
        assert any(row[0] == "ping" and row[2] == "FAIL" for row in rows)


class TestSpinner:
    @patch("scrapy_ingest.cli._MIN_SPIN", 0)
    @patch("scrapy_ingest.cli._progress")
    def test_run_spinner_animates(self, progress):
        result = _run_spinner("Testing", lambda: "done")
        assert result == "done"
        progress.assert_called()
        assert "|" in progress.call_args_list[0].args[0]

    @patch("scrapy_ingest.cli._MIN_SPIN", 0)
    @patch("scrapy_ingest.cli._progress")
    def test_run_spinner_raises_worker_error(self, progress):
        def boom():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            _run_spinner("Testing", boom)


class TestCheckConfigCommand:
    @patch("scrapy_ingest.cli.run_check_config", return_value=(True, []))
    @patch("scrapy_ingest.cli.info")
    def test_exit_code_zero_on_success(self, _info, _run):
        args = MagicMock(db_url=None, search_url=None)
        assert check_config_command(args) == 0

    @patch("scrapy_ingest.cli.run_check_config", return_value=(False, []))
    @patch("scrapy_ingest.cli.info")
    def test_exit_code_one_on_failure(self, _info, _run):
        args = MagicMock(db_url=None, search_url=None)
        assert check_config_command(args) == 1
