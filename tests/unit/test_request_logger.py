from unittest.mock import MagicMock, patch

import pytest

from scrapy_ingest.collector.collector import DataCollector
from scrapy_ingest.extensions.request_logger import (
    RequestLogger,
    _format_spider_error,
    _request_from_spider_error,
)


class TestSpiderErrorHelpers:
    def test_format_spider_error_includes_traceback(self):
        try:
            raise ValueError("bad parse")
        except ValueError as exc:
            failure = MagicMock()
            failure.value = exc
            failure.type = ValueError
            failure.getTraceback.return_value = "Traceback (most recent call last):\n  ..."

        text = _format_spider_error(failure)
        assert text.startswith("ValueError: bad parse")
        assert "Traceback" in text

    def test_request_from_spider_error_prefers_response_request(self):
        request = MagicMock()
        response = MagicMock(request=request)
        failure = MagicMock(request=None, value=None)
        assert _request_from_spider_error(failure, response) is request


class TestRequestLoggerSpiderError:
    def setup_method(self):
        self.collector = DataCollector()
        self.logger = RequestLogger()
        self.logger.crawler = MagicMock()
        self.logger.collector = self.collector

    def _failure(self, message="bad parse"):
        try:
            raise RuntimeError(message)
        except RuntimeError as exc:
            failure = MagicMock()
            failure.value = exc
            failure.type = RuntimeError
            failure.getTraceback.return_value = f"Traceback...\nRuntimeError: {message}"
            failure.request = None
            return failure

    def test_spider_error_updates_existing_request_row(self):
        request = MagicMock()
        request.url = "https://example.com/item"
        request.method = "GET"
        request.meta = {"start_time": 100.0}
        response = MagicMock(status=200, request=request)

        with patch(
            "scrapy_ingest.extensions.request_logger.get_request_fingerprint",
            return_value="fp-1",
        ):
            with patch(
                "scrapy_ingest.extensions.request_logger.get_parent_url",
                return_value="https://example.com",
            ):
                with patch("scrapy_ingest.extensions.request_logger.time.time", return_value=101.5):
                    self.logger.response_received(response, request, MagicMock())
                    self.logger.spider_error(self._failure(), response, MagicMock())

        assert len(self.collector.requests) == 1
        row = self.collector.requests[0]
        assert row["url"] == "https://example.com/item"
        assert row["status_code"] == 200
        assert row["success"] is False
        assert row["error"].startswith("RuntimeError: bad parse")
        assert "Traceback" in row["error"]

    def test_spider_error_adds_row_when_response_not_logged(self):
        request = MagicMock()
        request.url = "https://example.com/missed"
        request.method = "POST"
        request.meta = {"start_time": 10.0}
        response = MagicMock(status=500, request=request)

        with patch(
            "scrapy_ingest.extensions.request_logger.get_request_fingerprint",
            return_value="fp-2",
        ):
            with patch(
                "scrapy_ingest.extensions.request_logger.get_parent_url",
                return_value=None,
            ):
                with patch("scrapy_ingest.extensions.request_logger.time.time", return_value=12.0):
                    self.logger.spider_error(self._failure("missing row"), response, MagicMock())

        assert len(self.collector.requests) == 1
        row = self.collector.requests[0]
        assert row["url"] == "https://example.com/missed"
        assert row["method"] == "POST"
        assert row["status_code"] == 500
        assert row["success"] is False
        assert "missing row" in row["error"]

    def test_spider_error_skips_when_request_unavailable(self):
        failure = self._failure()
        response = MagicMock(spec=[])
        response.request = None

        self.logger.spider_error(failure, response, MagicMock())
        assert self.collector.requests == []


class TestDataCollectorMarkRequestError:
    def test_mark_request_error_updates_latest_matching_fingerprint(self):
        collector = DataCollector()
        collector.add_request({"fingerprint": "a", "error": None, "success": True})
        collector.add_request({"fingerprint": "b", "error": None, "success": True})
        collector.add_request({"fingerprint": "a", "error": None, "success": True})

        assert collector.mark_request_error("a", "parse failed") is True
        assert collector.requests[0]["error"] is None
        assert collector.requests[1]["error"] is None
        assert collector.requests[2]["error"] == "parse failed"
        assert collector.requests[2]["success"] is False

    def test_mark_request_error_returns_false_when_not_found(self):
        collector = DataCollector()
        assert collector.mark_request_error("missing", "err") is False
