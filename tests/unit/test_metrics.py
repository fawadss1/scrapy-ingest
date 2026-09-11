from scrapy_ingest.utils.metrics import (
    compute_errors_count,
    count_standalone_log_errors,
    sql_standalone_log_errors_clause,
)


class TestComputeErrorsCount:
    def test_failed_request_without_duplicate_scraper_log_counts_once(self):
        logs = [
            {"level": "INFO", "logger": "stdout", "message": "ok"},
            {
                "level": "ERROR",
                "logger": "scrapy.core.scraper",
                "message": "Spider error processing",
            },
        ]
        assert count_standalone_log_errors(logs) == 0
        assert compute_errors_count(failed_requests=1, standalone_log_errors=0) == 1

    def test_pipeline_error_counts_without_failed_request(self):
        logs = [{"level": "ERROR", "logger": "my.pipeline", "message": "boom"}]
        assert count_standalone_log_errors(logs) == 1
        assert compute_errors_count(failed_requests=0, standalone_log_errors=1) == 1

    def test_failed_request_and_unrelated_error_log(self):
        logs = [{"level": "CRITICAL", "logger": "my.spider", "message": "config"}]
        assert compute_errors_count(
            failed_requests=2,
            standalone_log_errors=count_standalone_log_errors(logs),
        ) == 3

    def test_sql_clause_excludes_scraper_logger(self):
        clause = sql_standalone_log_errors_clause()
        assert "scrapy.core.scraper" in clause
        assert "NOT IN" in clause
