"""Load and format job rows from the ingest database or search index."""

from contextlib import contextmanager

from ..exceptions import ConfigurationError, IngestConnectionError
from ..utils.console import format_table

_KEYS, _LABELS = zip(*(
    ("job_id", "job"),
    ("spider_name", "spider"),
    ("status", "status"),
    ("finish_reason", "reason"),
    ("started_at", "started"),
    ("finished_at", "finished"),
    ("requests_count", "requests"),
    ("success_requests", "ok"),
    ("failed_requests", "failed"),
    ("items_count", "items"),
    ("logs_count", "logs"),
    ("errors_count", "errors"),
    ("elapsed_seconds", "elapsed"),
    ("items_per_min", "rate"),
))

_LIST_KEYS = (
    "job_id",
    "spider_name",
    "status",
    "started_at",
    "finished_at",
    "items_count",
    "requests_count",
    "failed_requests",
    "errors_count",
)
_LIST_LABELS = ("job", "spider", "status", "started", "finished", "items", "requests", "failed", "errors")


def _fmt(key, val):
    if key in ("started_at", "finished_at"):
        if val is None:
            return "-"
        text = str(val).replace("T", " ")
        return text[:19] if len(text) > 19 else text
    if key == "elapsed_seconds":
        return f"{val or 0}s"
    if key == "items_per_min":
        return f"{val or 0} items/min"
    return "-" if val is None else str(val)


def _row_dict(keys, row):
    return dict(zip(keys, row))


def _normalize_job(doc, keys):
    return {key: doc.get(key) for key in keys} if doc else None


def _jobs_index(settings):
    return f"{settings.search_index_prefix}-{settings.db_jobs_table}"


def _require_destination(settings):
    if settings.ingest_to_database or settings.ingest_to_search:
        return
    raise ConfigurationError(
        "jobs show requires a destination: set DB_URL (or DB_* fields) and/or SEARCH_URL"
    )


def _fetchall(db, sql, params=()):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_job(db, settings, job_id):
    """Return a job dict keyed by column name, or ``None`` if not found."""
    row = db.execute(
        f"SELECT {', '.join(_KEYS)} FROM {settings.db_jobs_table} WHERE job_id = %s",
        (job_id,),
    )
    return _row_dict(_KEYS, row) if row else None


def fetch_job_search(client, settings, job_id):
    """Return a job dict from the search index, or ``None`` if not found."""
    doc = client.get_document(_jobs_index(settings), job_id)
    return _normalize_job(doc, _KEYS)


def fetch_jobs(db, settings, *, limit=50):
    """Return recent jobs from SQL, newest first."""
    table = settings.db_jobs_table
    cols = ", ".join(_LIST_KEYS)
    order = "started_at DESC, id DESC"
    if getattr(settings, "db_dialect", "postgres") != "mysql":
        order = "started_at DESC NULLS LAST, id DESC"
    rows = _fetchall(
        db,
        f"SELECT {cols} FROM {table} ORDER BY {order} LIMIT %s",
        (limit,),
    )
    return [_row_dict(_LIST_KEYS, row) for row in rows]


def fetch_jobs_search(client, settings, *, limit=50):
    """Return recent jobs from the search index, newest first."""
    docs = client.search_documents(_jobs_index(settings), size=limit)
    return [_normalize_job(doc, _LIST_KEYS) for doc in docs]


def format_job_show(job):
    """Format one job as a Field | Value table."""
    rows = [(label, _fmt(key, job.get(key))) for key, label in zip(_KEYS, _LABELS)]
    return "\n".join(("[scrapy-ingest] job summary", format_table(("Field", "Value"), rows)))


def format_jobs_list(jobs):
    """Format multiple jobs as one table."""
    rows = [tuple(_fmt(key, job.get(key)) for key in _LIST_KEYS) for job in jobs]
    title = "[scrapy-ingest] jobs"
    if not rows:
        return f"{title}\n(no jobs found)"
    return "\n".join((title, format_table(_LIST_LABELS, rows)))


@contextmanager
def _with_search(settings):
    from ..database.search import SearchClient

    client = SearchClient(settings)
    try:
        yield client
    except IngestConnectionError:
        raise
    except Exception as exc:
        raise IngestConnectionError(str(exc)) from exc
    finally:
        client.close()


def load_job_report(settings, job_id):
    """Load one job from SQL or search."""
    _require_destination(settings)
    if settings.ingest_to_database:
        from ..database.connection import DatabaseConnection

        db = DatabaseConnection(settings.db_url)
        try:
            job = fetch_job(db, settings, job_id)
            return (None, "") if job is None else (job, format_job_show(job))
        except IngestConnectionError:
            raise
        finally:
            db.close()

    with _with_search(settings) as client:
        job = fetch_job_search(client, settings, job_id)
        return (None, "") if job is None else (job, format_job_show(job))


def load_jobs_list(settings, *, limit=50):
    """Load recent jobs from SQL or search."""
    _require_destination(settings)
    if settings.ingest_to_database:
        from ..database.connection import DatabaseConnection

        db = DatabaseConnection(settings.db_url)
        try:
            return format_jobs_list(fetch_jobs(db, settings, limit=limit))
        except IngestConnectionError:
            raise
        finally:
            db.close()

    with _with_search(settings) as client:
        return format_jobs_list(fetch_jobs_search(client, settings, limit=limit))
