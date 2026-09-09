"""Command-line helpers for scrapy-ingest."""
import argparse
import sys
import threading
import time

from .config.settings import Settings, validate_settings
from .exceptions import ConfigurationError, IngestConnectionError
from .utils.console import format_table, info
from .utils.summary import display_database

_SPINNER, _MIN_SPIN, _WIDTH = "|/-\\", 0.5, 88
_VT = False


def _enable_vt():
    global _VT
    if _VT:
        return
    _VT = True
    if sys.platform != "win32":
        return
    try:
        import ctypes

        k = ctypes.windll.kernel32
        h, mode = k.GetStdHandle(-11), ctypes.c_ulong()
        k.GetConsoleMode(h, ctypes.byref(mode))
        k.SetConsoleMode(h, mode.value | 4)
    except Exception:
        pass


def _progress(text, *, done=False):
    _enable_vt()
    suffix = "\n" if done else ""
    sys.stdout.write(f"\r{text.ljust(_WIDTH)}{suffix}")
    sys.stdout.flush()


def _truncate(text, limit=72):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def _run_spinner(message, action):
    box = {}

    def worker():
        try:
            box["v"] = action()
        except Exception as exc:
            box["e"] = exc

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t0, i = time.monotonic(), 0
    while True:
        _progress(f"  {_SPINNER[i % 4]} {message}")
        if not t.is_alive() and time.monotonic() - t0 >= _MIN_SPIN:
            break
        time.sleep(0.12)
        i += 1
    t.join(120)
    if "e" in box:
        raise box["e"]
    return box.get("v")


def _load_crawler_settings(db_url=None, search_url=None):
    try:
        from scrapy.utils.project import get_project_settings

        crawler_settings = get_project_settings()
    except Exception:
        from scrapy.settings import Settings as ScrapySettings

        crawler_settings = ScrapySettings()
    for key, value in (("DB_URL", db_url), ("SEARCH_URL", search_url)):
        if value is not None:
            crawler_settings.set(key, value, priority="cmdline")
    return crawler_settings


def _ping_db(settings):
    from .database.connection import DatabaseConnection

    db = DatabaseConnection(settings.db_url)
    db.close()


def _ping_search(settings):
    from .database.search import SearchClient

    client = SearchClient(settings)
    client.ping()
    client.close()


def run_check_config(db_url=None, search_url=None, use_spinner=True):
    """Validate settings and ping configured database and search destinations."""
    rows, ok = [], True
    spin = use_spinner

    def run(msg, fn):
        return _run_spinner(msg, fn) if spin else fn()

    def finish(msg, status):
        if spin:
            _progress(f"  [{status}] {msg}", done=True)

    try:
        settings = run(
            "Loading Scrapy settings",
            lambda: Settings(_load_crawler_settings(db_url, search_url)),
        )
        finish("Loading Scrapy settings", "OK")
    except Exception:
        finish("Loading Scrapy settings", "FAIL")
        raise

    try:
        run("Validating configuration", lambda: validate_settings(settings) or True)
        rows.append(("config", "destinations", "OK", "at least one destination configured"))
        finish("Validating configuration", "OK")
    except ConfigurationError as exc:
        rows.append(("config", "destinations", "FAIL", _truncate(exc)))
        finish("Validating configuration", "FAIL")
        return False, rows

    for kind, enabled, url, skip, ping, ok_msg, info in (
        (
            "database",
            settings.ingest_to_database,
            settings.db_url,
            "Database ping",
            lambda: _ping_db(settings),
            "connected",
            ("tables", settings.db_jobs_table),
        ),
        (
            "search",
            settings.ingest_to_search,
            settings.search_url,
            "Search ping",
            lambda: _ping_search(settings),
            "cluster responded",
            ("indexes", settings.search_index_prefix),
        ),
    ):
        if not enabled:
            rows.append(("config", kind, "-", "not configured"))
            finish(skip, "SKIP")
            continue
        target = display_database(url)
        rows.append(("config", kind, "OK", target))
        label = f"Pinging {kind} ({target})"
        try:
            run(label, ping)
            rows.append(("ping", kind, "OK", ok_msg))
            finish(label, "OK")
        except IngestConnectionError as exc:
            ok = False
            rows.append(("ping", kind, "FAIL", _truncate(exc)))
            finish(label, "FAIL")
        rows.append((info[0], kind, "info", info[1]))

    return ok, rows


def check_config_command(args):
    ok, rows = run_check_config(db_url=args.db_url, search_url=args.search_url)
    info("")
    info(format_table(("Step", "Destination", "Status", "Detail"), rows))
    info("")
    info(
        "scrapy-ingest check-config: "
        + ("all configured destinations are reachable." if ok else "one or more checks failed.")
    )
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="scrapy-ingest")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-config", help="Validate DB_URL / SEARCH_URL and ping destinations")
    check.add_argument("--db-url", help="Override DB_URL from Scrapy settings")
    check.add_argument("--search-url", help="Override SEARCH_URL from Scrapy settings")
    check.set_defaults(func=check_config_command)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
