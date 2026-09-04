from unittest.mock import MagicMock, patch

from scrapy_ingest.database.flusher import IngestFlusher
from scrapy_ingest.utils.summary import display_database, format_crawl_summary


class TestFormatCrawlSummary:
    def test_includes_counts_and_labels(self):
        text = format_crawl_summary(
            {
                "job_id": "quotes-20260901120000-abcd1234",
                "spider": "quotes",
                "reason": "finished",
                "items_count": 120,
                "requests_count": 340,
                "success_requests": 320,
                "failed_requests": 20,
                "logs_count": 85,
                "errors_count": 22,
                "elapsed_seconds": 45.2,
                "items_per_min": 159.3,
                "database": "postgresql://localhost:5432/scrapy_data",
                "jobs_table": "jobs",
                "items_table": "job_items",
                "requests_table": "job_requests",
                "logs_table": "job_logs",
            }
        )

        assert text.startswith("[scrapy-ingest] crawl summary")
        assert "+-" in text
        assert "| Field    |" in text
        assert "| Metric   |" in text
        assert "quotes-20260901120000-abcd1234" in text
        assert "quotes" in text
        assert "finished" in text
        assert "postgresql://localhost:5432/scrapy_data" in text
        assert "job_items" in text
        assert "job_requests" in text
        assert "job_logs" in text
        assert "120" in text
        assert "340" in text
        assert "320" in text
        assert "20" in text
        assert "85" in text
        assert "22" in text
        assert "45.2s" in text
        assert "159.3 items/min" in text

    def test_uses_placeholders_when_fields_missing(self):
        text = format_crawl_summary({})
        assert "| job      | - " in text
        assert "| spider   | - " in text
        assert "| reason   | - " in text
        assert "| database | - " in text
        assert "| search   | - " in text
        assert "job_items" in text
        assert "job_requests" in text

    def test_display_database_strips_credentials(self):
        assert (
            display_database("postgresql://user:s3cret@localhost:5432/scrapy_data")
            == "postgresql://localhost:5432/scrapy_data"
        )
        assert display_database(None) == "-"
        assert display_database("") == "-"


class TestPrintSummary:
    def _flusher(self):
        settings = MagicMock()
        settings.db_url = "postgresql://user:s3cret@localhost:5432/scrapy_data"
        settings.db_jobs_table = "jobs"
        settings.db_items_table = "job_items"
        settings.db_requests_table = "job_requests"
        settings.db_logs_table = "job_logs"
        settings.ingest_show_summary = True
        settings.ingest_to_database = True
        settings.ingest_to_search = False
        flusher = IngestFlusher(crawler=MagicMock(), settings=settings)
        flusher.job_id = "job-1"
        flusher.spider_name = "quotes"
        return flusher

    def test_prints_once_to_stderr(self):
        flusher = self._flusher()
        metrics = {
            "reason": "finished",
            "items_count": 3,
            "requests_count": 5,
            "success_requests": 4,
            "failed_requests": 1,
            "logs_count": 2,
            "errors_count": 1,
            "elapsed_seconds": 1.5,
            "items_per_min": 120.0,
        }

        with patch("scrapy_ingest.database.flusher.info") as mock_info:
            flusher._print_summary(metrics)
            flusher._print_summary(metrics)

        mock_info.assert_called_once()
        text = mock_info.call_args.args[0]
        assert "[scrapy-ingest] crawl summary" in text
        assert "job-1" in text
        assert "postgresql://localhost:5432/scrapy_data" in text
        assert "job_items" in text
        assert "s3cret" not in text

    def test_skips_when_summary_disabled(self):
        flusher = self._flusher()
        flusher.settings.ingest_show_summary = False
        with patch("scrapy_ingest.database.flusher.info") as mock_info:
            flusher._print_summary(
                {
                    "reason": "finished",
                    "items_count": 1,
                    "requests_count": 1,
                    "success_requests": 1,
                    "failed_requests": 0,
                    "logs_count": 0,
                    "errors_count": 0,
                    "elapsed_seconds": 1,
                    "items_per_min": 60,
                }
            )
        mock_info.assert_not_called()

    def test_skips_empty_metrics(self):
        flusher = self._flusher()
        with patch("scrapy_ingest.database.flusher.info") as mock_info:
            flusher._print_summary(None)
        mock_info.assert_not_called()

    def test_finalize_prints_after_finish_job(self):
        flusher = self._flusher()
        flusher.job_pk = 7
        flusher.db_writer = MagicMock()
        flusher.db_writer.finish_job.return_value = {
            "reason": "finished",
            "items_count": 1,
            "requests_count": 2,
            "success_requests": 2,
            "failed_requests": 0,
            "logs_count": 0,
            "errors_count": 0,
            "elapsed_seconds": 0.5,
            "items_per_min": 120.0,
        }

        with patch("scrapy_ingest.database.flusher.info") as mock_info:
            flusher._finalize_job()

        flusher.db_writer.finish_job.assert_called_once()
        mock_info.assert_called_once()
        text = mock_info.call_args.args[0]
        assert "| Metric   |" in text
        assert "job_items" in text
