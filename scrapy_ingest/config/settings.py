"""
Module for managing and validating crawler settings.
"""
from urllib.parse import quote_plus


class Settings:
    """
    Handles settings configuration for crawlers, providing access to default values,
    database table names, and other operational parameters defined in crawler settings.
    """

    DEFAULT_ITEMS_TABLE = "job_items"
    DEFAULT_REQUESTS_TABLE = "job_requests"
    DEFAULT_LOGS_TABLE = "job_logs"
    DEFAULT_JOBS_TABLE = "jobs"
    DEFAULT_DB_TYPE = "postgres"
    DEFAULT_TIMEZONE = "Asia/Karachi"
    DEFAULT_BATCH_SIZE = 50
    DEFAULT_FLUSH_INTERVAL = 10.0
    DEFAULT_SHOW_SUMMARY = True
    DEFAULT_SEARCH_INDEX_PREFIX = "ingest"
    _DB_SCHEMES = {
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "mysql": "mysql",
        "mariadb": "mysql",
    }
    _DB_PORTS = {
        "postgres": 5432,
        "postgresql": 5432,
        "mysql": 3306,
        "mariadb": 3306,
    }
    _URL_DIALECTS = {
        "postgres": "postgres",
        "postgresql": "postgres",
        "mysql": "mysql",
        "mariadb": "mysql",
    }

    def __init__(self, crawler_settings):
        self.crawler_settings = crawler_settings

    @property
    def db_url(self):
        """Database URL from DB_URL, or built from discrete DB_* fields."""
        url = self.crawler_settings.get("DB_URL")
        if url:
            return url

        host = self.crawler_settings.get("DB_HOST")
        if not host:
            return None

        user = self.crawler_settings.get("DB_USER") or ""
        password = self.crawler_settings.get("DB_PASSWORD") or ""
        port = self.crawler_settings.get("DB_PORT", self._default_port())
        name = self.crawler_settings.get("DB_NAME") or ""
        scheme = self._DB_SCHEMES.get(self.db_type, self.db_type)
        return (
            f"{scheme}://{quote_plus(str(user))}:{quote_plus(str(password))}"
            f"@{host}:{port}/{name}"
        )

    @property
    def db_type(self):
        """Database engine from ``DB_TYPE`` (default: postgres)."""
        raw = self.crawler_settings.get("DB_TYPE", self.DEFAULT_DB_TYPE)
        if raw in (None, ""):
            return self.DEFAULT_DB_TYPE
        return str(raw).strip().lower()

    def _default_port(self):
        return self._DB_PORTS.get(self.db_type, 5432)

    @property
    def db_dialect(self):
        """``postgres`` or ``mysql``, from ``DB_URL`` scheme or ``DB_TYPE``."""
        url = self.crawler_settings.get("DB_URL")
        if url and "://" in str(url):
            scheme = str(url).split("://", 1)[0].lower().split("+")[0]
            if scheme in self._URL_DIALECTS:
                return self._URL_DIALECTS[scheme]
        if self.db_type in ("mysql", "mariadb"):
            return "mysql"
        return "postgres"

    @property
    def db_items_table(self):
        return self.crawler_settings.get("ITEMS_TABLE", self.DEFAULT_ITEMS_TABLE)

    @property
    def db_requests_table(self):
        return self.crawler_settings.get("REQUESTS_TABLE", self.DEFAULT_REQUESTS_TABLE)

    @property
    def db_logs_table(self):
        return self.crawler_settings.get("LOGS_TABLE", self.DEFAULT_LOGS_TABLE)

    @property
    def db_jobs_table(self):
        return (
            self.crawler_settings.get("JOBS_TABLE")
            or self.crawler_settings.get("DETAILS_TABLE")
            or self.DEFAULT_JOBS_TABLE
        )

    @property
    def create_tables(self):
        return self.crawler_settings.getbool("CREATE_TABLES", True)

    @property
    def ingest_batch_size(self):
        return self.crawler_settings.getint("INGEST_BATCH_SIZE", self.DEFAULT_BATCH_SIZE)

    @property
    def ingest_flush_interval(self):
        return self.crawler_settings.getfloat(
            "INGEST_FLUSH_INTERVAL", self.DEFAULT_FLUSH_INTERVAL
        )

    @property
    def ingest_show_summary(self):
        """Print the end-of-crawl summary table (default: True)."""
        return self.crawler_settings.getbool(
            "INGEST_SHOW_SUMMARY", self.DEFAULT_SHOW_SUMMARY
        )

    @property
    def ingest_to_database(self):
        return self.crawler_settings.getbool("INGEST_TO_DATABASE", True)

    @property
    def ingest_to_search(self):
        return self.crawler_settings.getbool("INGEST_TO_SEARCH", False)

    @property
    def search_url(self):
        return self.crawler_settings.get("SEARCH_URL")

    @property
    def search_user(self):
        return self.crawler_settings.get("SEARCH_USER")

    @property
    def search_password(self):
        return self.crawler_settings.get("SEARCH_PASSWORD")

    @property
    def search_index_prefix(self):
        return self.crawler_settings.get(
            "SEARCH_INDEX_PREFIX", self.DEFAULT_SEARCH_INDEX_PREFIX
        )

    @property
    def search_ssl_verify(self):
        return self.crawler_settings.getbool("SEARCH_SSL_VERIFY", True)

    def get_tz(self):
        return self.crawler_settings.get("TIMEZONE", self.DEFAULT_TIMEZONE)

    @staticmethod
    def get_identifier_column():
        return "job_id"

    def get_identifier_value(self, spider):
        """Use JOB_ID if set; otherwise a unique generated id (cached per crawl)."""
        from ..utils.job_id import cache_job_id, cached_job_id, generate_job_id

        configured = self.crawler_settings.get("JOB_ID", None)
        if configured not in (None, ""):
            return cache_job_id(spider, str(configured))

        existing = cached_job_id(spider)
        if existing:
            return existing

        return cache_job_id(spider, generate_job_id(getattr(spider, "name", "spider")))


def validate_settings(settings):
    """Validate the configured ingest destinations."""
    if not settings.ingest_to_database and not settings.ingest_to_search:
        raise ValueError(
            "Enable at least one destination: INGEST_TO_DATABASE and/or INGEST_TO_SEARCH"
        )
    if settings.ingest_to_database:
        url = settings.crawler_settings.get("DB_URL")
        if url and "://" in str(url):
            scheme = str(url).split("://", 1)[0].lower().split("+")[0]
            if scheme not in settings._URL_DIALECTS:
                supported = ", ".join(sorted(settings._URL_DIALECTS))
                raise ValueError(
                    f"Unsupported database URL scheme {scheme!r}. Supported: {supported}"
                )
        elif settings.db_type not in settings._DB_SCHEMES:
            supported = ", ".join(sorted(settings._DB_SCHEMES))
            raise ValueError(
                f"Unsupported DB_TYPE={settings.db_type!r}. Supported: {supported}"
            )
        if not settings.db_url:
            raise ValueError(
                "Database connection is required: set DB_URL or "
                "DB_HOST / DB_USER / DB_PASSWORD / DB_NAME"
            )
    if settings.ingest_to_search and not settings.search_url:
        raise ValueError("SEARCH_URL is required when INGEST_TO_SEARCH is True")
    return True
