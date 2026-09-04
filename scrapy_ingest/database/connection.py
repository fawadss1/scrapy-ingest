# scrapy_ingest/database/connection.py

import logging
from typing import Optional, Any, Sequence
from urllib.parse import quote, unquote, urlparse

from ..exceptions import DependencyError, IngestConnectionError


class DBConnection:
    """
    Database connection manager (singleton) for PostgreSQL and MySQL.
    Supports a DSN/URL or settings-based configuration and exposes
    ``connect/execute/commit/rollback/close``.
    """

    _instance: Optional["DBConnection"] = None
    _connection = None
    _db_url: Optional[str] = None
    _logger = logging.getLogger(__name__)

    def __new__(cls, db_url: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(DBConnection, cls).__new__(cls)
            if db_url:
                cls._instance._db_url = db_url
            cls._instance._initialize_connection()
        return cls._instance

    @staticmethod
    def _is_mysql_url(url):
        if not url or "://" not in str(url):
            return False
        scheme = str(url).split("://", 1)[0].lower().split("+")[0]
        return scheme in ("mysql", "mariadb")

    def _normalize_dsn(self, dsn: str) -> str:
        """URL-encode credentials if the password contains reserved characters."""
        try:
            if "://" not in dsn:
                return dsn
            scheme, rest = dsn.split("://", 1)
            if "/" in rest:
                netloc, tail = rest.split("/", 1)
                tail = "/" + tail
            else:
                netloc, tail = rest, ""
            if "@" in netloc:
                userinfo, hostport = netloc.rsplit("@", 1)
                if ":" in userinfo:
                    user, pwd = userinfo.split(":", 1)
                    if any(c in pwd for c in "@:$ /\\"):
                        user_enc = quote(unquote(user), safe="")
                        pwd_enc = quote(pwd, safe="")
                        netloc = f"{user_enc}:{pwd_enc}@{hostport}"
            return f"{scheme}://{netloc}{tail}"
        except Exception:
            return dsn

    def _is_open(self):
        conn = self._connection
        if conn is None:
            return False
        if hasattr(conn, "closed"):
            return conn.closed == 0
        return bool(getattr(conn, "open", False))

    def _connect_postgres(self, dsn=None, **kwargs):
        import psycopg2

        if dsn:
            return psycopg2.connect(dsn)
        return psycopg2.connect(**kwargs)

    def _connect_mysql(self, dsn=None, **kwargs):
        try:
            import pymysql
        except ImportError as exc:
            raise DependencyError(
                "MySQL support requires PyMySQL. Reinstall scrapy-ingest to get it."
            ) from exc
        if dsn:
            parsed = urlparse(dsn)
            kwargs = {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 3306,
                "user": unquote(parsed.username or ""),
                "password": unquote(parsed.password or ""),
                "database": unquote((parsed.path or "").lstrip("/").split("?")[0]),
                "charset": "utf8mb4",
            }
        kwargs.setdefault("autocommit", False)
        return pymysql.connect(**kwargs)

    def _connect_error_types(self):
        errors = []
        try:
            from psycopg2 import OperationalError as PgError

            errors.append(PgError)
        except ImportError:
            pass
        try:
            from pymysql import OperationalError as MyError

            errors.append(MyError)
        except ImportError:
            pass
        return tuple(errors) or (Exception,)

    def _initialize_connection(self):
        """Initialize the connection once (or reconnect if closed)."""
        if self._is_open():
            return

        source = "unknown"
        try:
            if self._db_url:
                source = "db_url"
                dsn = self._normalize_dsn(self._db_url)
                if self._is_mysql_url(dsn):
                    self._connection = self._connect_mysql(dsn)
                else:
                    self._connection = self._connect_postgres(dsn)
            else:
                from scrapy.utils.project import get_project_settings

                settings = get_project_settings()
                source = "Scrapy settings"
                db_type = str(settings.get("DB_TYPE") or "postgres").strip().lower()
                kwargs = {
                    "host": settings.get("DB_HOST"),
                    "port": settings.get("DB_PORT"),
                    "user": settings.get("DB_USER"),
                    "password": settings.get("DB_PASSWORD"),
                }
                if db_type in ("mysql", "mariadb"):
                    kwargs["database"] = settings.get("DB_NAME")
                    self._connection = self._connect_mysql(**kwargs)
                else:
                    kwargs["dbname"] = settings.get("DB_NAME")
                    self._connection = self._connect_postgres(**kwargs)
            if hasattr(self._connection, "autocommit"):
                try:
                    self._connection.autocommit = False
                except Exception:
                    pass
        except self._connect_error_types() as e:
            self._logger.error(
                "Failed to connect to database via %s: %s. "
                "Verify DB settings or DSN (host, port, user, dbname).",
                source,
                str(e),
            )
            raise IngestConnectionError(
                f"Failed to connect to database via {source}: {e}"
            ) from e
        except Exception as e:
            self._logger.error(
                "Failed to connect to database via %s: %s. "
                "Verify DB settings or DSN (host, port, user, dbname).",
                source,
                str(e),
            )
            raise IngestConnectionError(
                f"Failed to connect to database via {source}: {e}"
            ) from e

    def connect(self) -> bool:
        try:
            self._initialize_connection()
            return True
        except IngestConnectionError:
            return False

    def cursor(self):
        if not self._is_open():
            self._initialize_connection()
        return self._connection.cursor()

    def execute(self, sql: str, params: Sequence[Any] = None):
        """Execute a SQL statement.
        Returns the first row if the statement produces a result set,
        otherwise returns None.
        """
        with self.cursor() as cur:
            if params is not None:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            if cur.description is not None:
                return cur.fetchone()
            return None

    def executemany(self, sql: str, params_seq):
        with self.cursor() as cur:
            cur.executemany(sql, params_seq)

    def commit(self):
        if self._connection:
            self._connection.commit()

    def rollback(self):
        if self._connection:
            self._connection.rollback()

    def close(self):
        if self._is_open():
            self._connection.close()


DatabaseConnection = DBConnection
