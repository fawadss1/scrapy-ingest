from unittest.mock import MagicMock, patch

import pytest

from scrapy_ingest.cli import jobs_show_command, run_jobs_show
from scrapy_ingest.exceptions import ConfigurationError
from scrapy_ingest.jobs.show import (
    fetch_job,
    fetch_jobs,
    format_job_show,
    format_jobs_list,
    load_job_report,
    load_jobs_list,
)


_JOB = {
    "job_id": "spider-123",
    "spider_name": "demo",
    "status": "finished",
    "finish_reason": "finished",
    "started_at": "2026-09-09 10:00:00",
    "finished_at": "2026-09-09 10:05:00",
    "items_count": 3,
    "requests_count": 5,
    "success_requests": 4,
    "failed_requests": 1,
    "logs_count": 20,
    "errors_count": 1,
    "elapsed_seconds": 300.0,
    "items_per_min": 0.6,
}

_LIST_JOB = {k: _JOB[k] for k in (
    "job_id", "spider_name", "status", "started_at", "finished_at",
    "items_count", "requests_count", "failed_requests", "errors_count",
)}


def _settings(**values):
    crawler_settings = MagicMock()
    crawler_settings.get.side_effect = lambda key, default=None: values.get(key, default)
    crawler_settings.getbool.side_effect = lambda key, default=False: values.get(key, default)
    return crawler_settings


class TestFormatJobShow:
    def test_shows_jobs_table_columns_only(self):
        text = format_job_show(_JOB)
        assert "spider-123" in text and "demo" in text
        assert "| Field " in text and "| Value " in text
        assert "| job " in text and "| items " in text
        assert "| HTTP " not in text and "database" not in text.lower()


class TestFormatJobsList:
    def test_formats_multiple_jobs(self):
        text = format_jobs_list([_LIST_JOB])
        assert "[scrapy-ingest] jobs" in text
        assert "spider-123" in text and "| spider " in text

    def test_empty_list(self):
        assert "(no jobs found)" in format_jobs_list([])


class TestLoadJobReport:
    @patch("scrapy_ingest.database.connection.DatabaseConnection")
    def test_returns_none_when_job_missing(self, db_cls):
        db = db_cls.return_value
        db.execute.return_value = None
        settings = MagicMock(ingest_to_database=True, db_url="postgresql://localhost/db", db_jobs_table="jobs")
        job, report = load_job_report(settings, "missing-id")
        assert job is None and report == ""
        db.close.assert_called_once()

    def test_requires_destination(self):
        with pytest.raises(ConfigurationError, match="requires a destination"):
            load_job_report(MagicMock(ingest_to_database=False, ingest_to_search=False), "job-1")


class TestLoadJobsList:
    @patch("scrapy_ingest.jobs.show.fetch_jobs", return_value=[_LIST_JOB])
    @patch("scrapy_ingest.database.connection.DatabaseConnection")
    def test_returns_formatted_list(self, db_cls, _fetch):
        settings = MagicMock(ingest_to_database=True, db_url="postgresql://localhost/db", db_jobs_table="jobs")
        text = load_jobs_list(settings)
        assert "spider-123" in text
        db_cls.return_value.close.assert_called_once()

    @patch("scrapy_ingest.jobs.show.fetch_jobs_search", return_value=[_LIST_JOB])
    @patch("scrapy_ingest.jobs.show._with_search")
    def test_loads_from_search_when_no_database(self, search_ctx, _fetch):
        client = search_ctx.return_value.__enter__.return_value
        settings = MagicMock(
            ingest_to_database=False,
            ingest_to_search=True,
            search_index_prefix="ingest",
            db_jobs_table="jobs",
        )
        text = load_jobs_list(settings)
        assert "spider-123" in text
        search_ctx.return_value.__enter__.assert_called_once()
        _fetch.assert_called_once_with(client, settings, limit=50)


class TestFetchJob:
    def test_selects_jobs_table_columns(self):
        db = MagicMock()
        db.execute.return_value = tuple(_JOB[k] for k in (
            "job_id", "spider_name", "status", "finish_reason", "started_at", "finished_at",
            "requests_count", "success_requests", "failed_requests", "items_count",
            "logs_count", "errors_count", "elapsed_seconds", "items_per_min",
        ))
        job = fetch_job(db, MagicMock(db_jobs_table="jobs"), "spider-123")
        assert job["job_id"] == "spider-123" and job["items_count"] == 3


class TestFetchJobs:
    def test_fetches_recent_jobs(self):
        db = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [tuple(_LIST_JOB[k] for k in (
            "job_id", "spider_name", "status", "started_at", "finished_at",
            "items_count", "requests_count", "failed_requests", "errors_count",
        ))]
        db.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        db.cursor.return_value.__exit__ = MagicMock(return_value=False)
        jobs = fetch_jobs(db, MagicMock(db_jobs_table="jobs"), limit=10)
        assert len(jobs) == 1 and jobs[0]["job_id"] == "spider-123"
        assert "LIMIT %s" in cur.execute.call_args[0][0]


class TestRunJobsShow:
    @patch("scrapy_ingest.cli.load_job_report", return_value=({"job_id": "j1"}, "report"))
    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_returns_report_when_job_found(self, load_settings, _load_report):
        load_settings.return_value = _settings(DB_URL="postgresql://localhost/db")
        job, report, error = run_jobs_show("j1", use_spinner=False)
        assert error is None and job["job_id"] == "j1" and report == "report"

    @patch("scrapy_ingest.cli.load_jobs_list", return_value="jobs list")
    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_lists_jobs_when_no_job_id(self, load_settings, load_list):
        load_settings.return_value = _settings(DB_URL="postgresql://localhost/db")
        job, report, error = run_jobs_show(use_spinner=False)
        assert error is None and job is None and report == "jobs list"
        load_list.assert_called_once()

    @patch("scrapy_ingest.cli.load_job_report", return_value=(None, ""))
    @patch("scrapy_ingest.cli._load_crawler_settings")
    def test_returns_error_when_job_missing(self, load_settings, _load_report):
        load_settings.return_value = _settings(DB_URL="postgresql://localhost/db")
        job, _, error = run_jobs_show("missing", use_spinner=False)
        assert job is None and "not found" in error


class TestJobsShowCommand:
    @patch("scrapy_ingest.cli.run_jobs_show", return_value=({"job_id": "j1"}, "report", None))
    @patch("scrapy_ingest.cli.info")
    def test_exit_zero_when_job_found(self, info, _run):
        assert jobs_show_command(MagicMock(job_id="j1", db_url=None, limit=50)) == 0
        info.assert_called_once_with("\nreport\n")

    @patch("scrapy_ingest.cli.run_jobs_show", return_value=(None, "jobs list", None))
    @patch("scrapy_ingest.cli.info")
    def test_exit_zero_when_listing_jobs(self, info, _run):
        assert jobs_show_command(MagicMock(job_id=None, db_url=None, limit=50)) == 0
        info.assert_called_once_with("\njobs list\n")

    @patch("scrapy_ingest.cli.run_jobs_show", return_value=(None, None, "job not found: missing"))
    @patch("scrapy_ingest.cli.info")
    def test_exit_one_when_job_missing(self, info, _run):
        assert jobs_show_command(MagicMock(job_id="missing", db_url=None, limit=50)) == 1
        assert "not found" in info.call_args[0][0]
