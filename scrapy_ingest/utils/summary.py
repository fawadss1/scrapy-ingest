"""Format the end-of-crawl ingest summary printed when the spider closes."""

from urllib.parse import urlparse

from .console import format_table


def display_database(url):
    """Return host:port/dbname from a DSN, with credentials stripped."""
    if not isinstance(url, str) or not url.strip():
        return "-"
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    name = (parsed.path or "").lstrip("/").split("?")[0]
    scheme = parsed.scheme or "postgresql"
    if host and name:
        return f"{scheme}://{host}{port}/{name}"
    if name:
        return name
    return host or "-"


def format_crawl_summary(summary):
    """Return a tabular crawl recap from finalized job metrics."""
    jobs_table = summary.get("jobs_table") or "jobs"
    items_table = summary.get("items_table") or "job_items"
    requests_table = summary.get("requests_table") or "job_requests"
    logs_table = summary.get("logs_table") or "job_logs"
    elapsed = summary.get("elapsed_seconds", 0)
    rate = summary.get("items_per_min", 0)
    crawl = format_table(
        ("Field", "Value"),
        (
            ("job", summary.get("job_id") or "-"),
            ("spider", summary.get("spider") or "-"),
            ("reason", summary.get("reason") or "-"),
            ("database", summary.get("database") or "-"),
        ),
    )
    inserted = format_table(
        ("Metric", "Count", "Table"),
        (
            ("jobs", 1, jobs_table),
            ("items", summary.get("items_count", 0), items_table),
            ("requests", summary.get("requests_count", 0), requests_table),
            ("ok", summary.get("success_requests", 0), "-"),
            ("failed", summary.get("failed_requests", 0), "-"),
            ("logs", summary.get("logs_count", 0), logs_table),
            ("errors", summary.get("errors_count", 0), "-"),
            ("elapsed", f"{elapsed}s", "-"),
            ("rate", f"{rate} items/min", "-"),
        ),
    )
    return "\n".join(("[scrapy-ingest] crawl summary", crawl, inserted))
