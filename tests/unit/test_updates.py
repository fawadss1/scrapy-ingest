import json
from unittest.mock import MagicMock, patch

import pytest

from scrapy_ingest.utils import updates

_IMPL = "scrapy_ingest.utils.updates"


def _pypi_payload(version: str, project_url: str | None = None) -> dict:
    return {
        "info": {
            "version": version,
            "project_url": project_url or "https://pypi.org/project/scrapy-ingest/",
        }
    }


class TestGetUpdateUrl:
    def test_returns_none_when_current_is_latest(self):
        payload = _pypi_payload("1.0.0")
        with patch(f"{_IMPL}.latest_pypi_release", return_value=payload):
            assert updates.get_update_url("1.0.0") is None

    def test_returns_url_when_newer_release_exists(self):
        payload = _pypi_payload("2.0.0")
        with patch(f"{_IMPL}.latest_pypi_release", return_value=payload):
            url = updates.get_update_url("1.0.0")
        assert url == "https://pypi.org/project/scrapy-ingest/2.0.0/"

    def test_handles_prerelease_versions(self):
        payload = _pypi_payload("0.7.0")
        with patch(f"{_IMPL}.latest_pypi_release", return_value=payload):
            assert (
                updates.get_update_url("0.6.10a1")
                == "https://pypi.org/project/scrapy-ingest/0.7.0/"
            )

    def test_silent_fail_on_network_error(self):
        with patch(
            f"{_IMPL}.latest_pypi_release",
            side_effect=OSError("network down"),
        ):
            assert updates.get_update_url("1.0.0") is None

    def test_raises_when_silent_fail_disabled(self):
        with patch(
            f"{_IMPL}.latest_pypi_release",
            side_effect=OSError("network down"),
        ):
            with pytest.raises(OSError, match="network down"):
                updates.get_update_url("1.0.0", silent_fail=False)


class TestLatestPypiRelease:
    def test_fetches_pypi_project_json(self):
        payload = _pypi_payload("1.2.3")
        body = json.dumps(payload).encode()

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return body

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as mock_open:
            result = updates.latest_pypi_release("scrapy-ingest")

        assert result == payload
        request = mock_open.call_args.args[0]
        assert request.full_url == "https://pypi.org/pypi/scrapy-ingest/json"


class TestUpdateAvailable:
    def setup_method(self):
        updates._reset_update_check_state()

    def teardown_method(self):
        updates._reset_update_check_state()

    def test_runs_check_once_per_process(self):
        def run_target_immediately(*, target, **kwargs):
            target()
            return MagicMock()

        with (
            patch(f"{_IMPL}.get_update_url", return_value=None) as mock_check,
            patch(f"{_IMPL}.threading.Thread", side_effect=run_target_immediately),
        ):
            updates.update_available()
            updates.update_available()
        mock_check.assert_called_once()

    def test_notifies_when_update_exists(self):
        url = "https://pypi.org/project/scrapy-ingest/9.9.9/"
        with (
            patch(f"{_IMPL}.get_update_url", return_value=url),
            patch(f"{_IMPL}.print") as mock_print,
        ):
            updates._notify_if_update_available()

        mock_print.assert_called_once()
        message = mock_print.call_args.args[0]
        assert url in message
        assert "pip install -U scrapy-ingest" in message
        assert mock_print.call_args.kwargs["file"] is updates.sys.stderr


class TestStartupHooks:
    def test_enable_ingest_triggers_update_check(self):
        crawler = MagicMock()
        crawler._ingest_enabled = False

        with (
            patch("scrapy_ingest.bootstrap.bootstrap.LoggingExtension"),
            patch("scrapy_ingest.bootstrap.bootstrap.StatsExtension"),
            patch("scrapy_ingest.bootstrap.bootstrap.RequestLogger"),
            patch("scrapy_ingest.bootstrap.bootstrap.ensure_collector"),
            patch("scrapy_ingest.bootstrap.bootstrap.attach_runtime_hooks"),
            patch("scrapy_ingest.bootstrap.bootstrap.update_available") as mock_check,
        ):
            from scrapy_ingest.bootstrap.bootstrap import enable_ingest

            enable_ingest(crawler)

        mock_check.assert_called_once_with()

    def test_items_pipeline_triggers_update_check(self):
        crawler = MagicMock()
        settings = MagicMock()
        settings.db_type = "postgres"
        settings._DB_SCHEMES = {"postgres": "postgresql"}
        settings.db_url = "postgresql://localhost/test"

        with (
            patch("scrapy_ingest.pipelines.items.ensure_collector"),
            patch("scrapy_ingest.pipelines.items.Settings", return_value=settings),
            patch("scrapy_ingest.pipelines.items.update_available") as mock_check,
        ):
            from scrapy_ingest.pipelines.items import ItemsPipeline

            ItemsPipeline.from_crawler(crawler)

        mock_check.assert_called_once_with()
