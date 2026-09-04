Changelog
=========

[Unreleased]
------------

[1.2.0] - 2026-09-04
--------------------

### Added
- Optional Elasticsearch / OpenSearch indexing via ``SEARCH_URL``. Works alongside Postgres/MySQL (``DB_URL`` / ``DB_*``) or on its own. Uses ``opensearch-py`` (compatible with Elasticsearch and OpenSearch REST APIs).
- Typed exception hierarchy (``IngestError``, ``ConfigurationError``, ``IngestConnectionError``, ``DatabaseError``, ``SchemaError``, ``SearchError``, ``DependencyError``, ``FlushError``) exported from ``scrapy_ingest``.

### Changed
- Ingest destination is inferred from connection settings: ``DB_URL`` (or ``DB_*``) enables SQL, ``SEARCH_URL`` enables Elasticsearch/OpenSearch, both enables dual-write. ``INGEST_TO_DATABASE`` and ``INGEST_TO_SEARCH`` are removed.
- Request duration is stored as ``response_time_secs`` (was ``response_time``) in ``job_requests`` and Elasticsearch/OpenSearch indexes so the unit is explicit.

[1.1.1] - 2026-09-02
--------------------

### Changed
- Dropped unused ``SQLAlchemy`` dependency. Connections stay on ``psycopg2`` and ``PyMySQL``.
- PyPI update check compares versions without the ``packaging`` dependency.

[1.1.0] - 2026-09-02
--------------------

### Added
- Automatic PyPI update check when a pipeline or extension loads. If a newer ``scrapy-ingest`` is published, a notice is printed to stderr (independent of Scrapy ``LOG_LEVEL``) with ``pip install -U scrapy-ingest`` and a release link. Network errors are silent and never interrupt crawling. The notice is not stored in ``job_logs``.
- End-of-crawl summary printed as ASCII tables when the spider closes: job, spider, finish reason, database (credentials stripped), tables, items, requests, ok/failed, logs, errors, elapsed time, and items/min. Shown even when ``LOG_LEVEL`` is ``ERROR``, and not stored in ``job_logs``. Disable with ``INGEST_SHOW_SUMMARY = False``.
- MySQL / MariaDB support alongside PostgreSQL (``DB_URL = mysql://...`` / ``mariadb://...``, or ``DB_TYPE = mysql`` / ``mariadb``). ``PyMySQL`` is installed with the package; no extra is required.
- Shared stderr console helper so update notices and the crawl summary stay visible at any log level and are not captured as job logs.

### Changed
- Auto-generated ``job_id`` now uses unix time plus a 4-character suffix (``Rs_Spider-178826754-a1b2``) instead of ``spider-YYYYMMDDHHMMSS-xxxxxxxx``.
- Table setup is ``CREATE TABLE IF NOT EXISTS`` only. Legacy ``ALTER TABLE`` / column-migration helpers were removed.
- Postgres vs MySQL SQL (upserts, types, parent-id linking) lives in the writer, schema, and connection modules.
- Minimum dependency versions updated: Scrapy 2.18, psycopg2-binary 2.9.12, itemadapter 0.13.1, SQLAlchemy 2.0.52, pytz 2026.3, w3lib 2.4.1, packaging 26.0, PyMySQL 1.2. Python 3.10+ is required (classifiers 3.10–3.14).
- Sphinx docs copyright year is taken from the current date.

### Fixed
- MySQL flush no longer fails when linking ``parent_id`` (error 1093: cannot update the same table used in a subquery). Parent rows are resolved with a join instead of a same-table subquery.

[1.0.0] - 2026-09-01
--------------------

First stable release of ``scrapy-ingest``.

### Added
- Shared batch collector for items, requests, logs, and stats (flush on batch size, every 10s, and engine stop)
- Automatic enable of request logging, error logging, parent_url tracking, job logs, and stats from ``DbInsertPipeline`` alone
- Crawl-graph ``parent_url`` via scraper hooks and a fingerprint map (start URLs are ``null``)
- Failed-request capture through injected error middleware (``error`` + ``success`` columns)
- Full job logs: early/startup buffer, Scrapy/Twisted/warnings, exceptions, and ``print()`` capture
- Scrapy crawl stats stored on ``jobs.stats``
- ``INGEST_BATCH_SIZE`` and ``INGEST_FLUSH_INTERVAL`` settings
- Discrete ``DB_*`` fields now build a connection URL (no ``DB_URL`` required)
- ``DB_TYPE`` setting (default: ``postgres``) used when building a URL from discrete fields
- Auto-generated unique ``job_id`` when ``JOB_ID`` is not set (``spider-YYYYMMDDHHMMSS-xxxxxxxx``)
- ``jobs`` table with per-crawl status, item/request/error/log counts, crawl speed, finish reason, and stats
- Child tables store ``jobs.id`` (integer) in ``job_id``, with ``ON DELETE CASCADE``

### Changed
- Package renamed to ``scrapy-ingest`` (import ``scrapy_ingest``). ``pip install scrapy-ingest``
- Recommended enable path is ``scrapy_ingest.pipelines.DbInsertPipeline``
- Request fingerprint is SHA1 of method + canonical URL (used for parent_url lookup)
- ``LoggingExtension`` follows Scrapy ``LOG_LEVEL``
- Items are buffered and batch-inserted instead of one commit per item
- ``parent_id`` is set from ``parent_url`` after each request flush
- Documentation uses the default Read the Docs theme so text stays readable
