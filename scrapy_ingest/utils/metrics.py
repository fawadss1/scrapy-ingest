"""Job metric helpers shared by SQL and search writers."""

ERROR_LEVELS = frozenset({"ERROR", "CRITICAL"})

# Scrapy loggers that repeat failures already stored on job_requests.
DUPLICATE_ERROR_LOGGERS = frozenset({"scrapy.core.scraper"})


def count_standalone_log_errors(log_entries):
    """Count ERROR/CRITICAL logs that are not request-level duplicates."""
    return sum(
        1
        for entry in log_entries
        if entry.get("level") in ERROR_LEVELS
        and entry.get("logger") not in DUPLICATE_ERROR_LOGGERS
    )


def compute_errors_count(failed_requests, standalone_log_errors):
    """Return total distinct errors for a job."""
    return int(failed_requests or 0) + int(standalone_log_errors or 0)


def sql_standalone_log_errors_clause():
    """SQL fragment excluding duplicate request error loggers."""
    names = ", ".join(f"'{name}'" for name in sorted(DUPLICATE_ERROR_LOGGERS))
    return (
        "AND level IN ('ERROR', 'CRITICAL') "
        f"AND (logger IS NULL OR logger NOT IN ({names}))"
    )
