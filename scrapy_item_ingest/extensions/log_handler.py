"""Log handler + early buffer + print capture for full job logs."""
from __future__ import annotations

import logging
import sys
import threading
from datetime import datetime, timezone

_lock = threading.Lock()
_early: logging.Handler | None = None
_buf: list = []
_skip = ("urllib3.", "requests.", "scrapy_item_ingest.", "psycopg2.")
_stdout_wrap = None


def _entry(record: logging.LogRecord) -> dict:
    try:
        msg = record.getMessage()
    except Exception:
        msg = str(record.msg)
    exc = None
    if record.exc_info:
        try:
            exc = logging.Formatter().formatException(record.exc_info)
        except Exception:
            pass
    ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
    return {
        "time": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "level": record.levelname,
        "logger": record.name,
        "message": msg,
        "exception": exc,
    }


def _keep(record: logging.LogRecord, min_level=logging.INFO) -> bool:
    return record.levelno >= min_level and not any(
        record.name.startswith(p) for p in _skip
    )


class _BufferHandler(logging.Handler):
    def emit(self, record):
        try:
            record.msg, record.args = record.getMessage(), ()
        except Exception:
            pass
        with _lock:
            _buf.append(record)


class IngestLogHandler(logging.Handler):
    """Writes Scrapy/user log records into the shared DataCollector."""

    def __init__(self, collector, level=logging.INFO):
        super().__init__(level)
        self.collector = collector
        self._busy = False

    def emit(self, record):
        if self._busy or not _keep(record, self.level):
            return
        self._busy = True
        try:
            self.collector.add_log(_entry(record))
        except Exception:
            self.handleError(record)
        finally:
            self._busy = False


def install_early():
    """Buffer root logs until the logging extension attaches the real handler."""
    global _early
    with _lock:
        if _early is not None:
            return
        _early = _BufferHandler()
        root = logging.getLogger()
        root.addHandler(_early)
        if root.level == logging.NOTSET or root.level > logging.INFO:
            root.setLevel(logging.INFO)
    try:
        import scrapy.utils.log as slog

        if not getattr(slog, "_ingest_patched", False):
            _orig = slog.configure_logging

            def _wrap(*a, **k):
                install_early()
                return _orig(*a, **k)

            slog.configure_logging = _wrap
            slog._ingest_patched = True
    except ImportError:
        pass


def drain_early(collector, min_level=logging.INFO):
    """Replay buffered startup logs into the crawl collector."""
    global _early
    with _lock:
        handler, records = _early, list(_buf)
        _buf.clear()
        _early = None
        if handler:
            root = logging.getLogger()
            if handler in root.handlers:
                root.removeHandler(handler)
    for record in records:
        if _keep(record, min_level):
            collector.add_log(_entry(record))


class _Stdout:
    def __init__(self, collector, original):
        self.collector = collector
        self.original = original
        self._line = ""

    def write(self, data):
        if not isinstance(data, str):
            data = data.decode("utf-8", errors="replace")
        if self.original:
            try:
                self.original.write(data)
            except Exception:
                pass
        if not data:
            return
        self._line += data
        while "\n" in self._line:
            line, self._line = self._line.split("\n", 1)
            line = line.rstrip("\r")
            if not line:
                continue
            if " [" in line and "] " in line and any(
                t in line for t in ("INFO:", "WARNING:", "ERROR:", "DEBUG:", "CRITICAL:")
            ):
                continue
            now = datetime.now(tz=timezone.utc)
            self.collector.add_log(
                {
                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "INFO",
                    "logger": "stdout",
                    "message": line,
                    "exception": None,
                }
            )

    def flush(self):
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass

    def isatty(self):
        return bool(getattr(self.original, "isatty", lambda: False)())

    @property
    def encoding(self):
        return getattr(self.original, "encoding", "utf-8")


def capture_prints(collector):
    global _stdout_wrap
    if _stdout_wrap is not None:
        return
    _stdout_wrap = _Stdout(collector, sys.stdout)
    sys.stdout = _stdout_wrap


def stop_prints():
    global _stdout_wrap
    if _stdout_wrap is None:
        return
    if sys.stdout is _stdout_wrap:
        sys.stdout = _stdout_wrap.original
    _stdout_wrap = None


install_early()
