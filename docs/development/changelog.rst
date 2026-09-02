Changelog
=========

[Unreleased]
------------

### Added
- Automatic PyPI update check when a pipeline or extension loads. If a newer ``scrapy-ingest`` is published, a notice is printed (independent of Scrapy ``LOG_LEVEL``) with ``pip install -U scrapy-ingest`` and a release link. Network errors are silent and never interrupt crawling.
- End-of-crawl summary printed as ASCII tables when the spider closes (job, database, tables, items, requests, logs, errors, elapsed time). Shown even when ``LOG_LEVEL`` is ``ERROR``, and not stored in ``job_logs``. Credentials are stripped from the database URL. Disable with ``INGEST_SHOW_SUMMARY = False``.
- MySQL / MariaDB support alongside PostgreSQL (``DB_URL = mysql://...`` or ``DB_TYPE = mysql``). ``PyMySQL`` is installed with the package.

### Changed
- Auto-generated ``job_id`` now uses unix time like item ``crawled_at`` plus a short unique suffix (``Rs_Spider-178826754-a1b2c3``) instead of ``spider-YYYYMMDDHHMMSS-xxxxxxxx``.
- Minimum dependency versions updated: Scrapy 2.18, psycopg2-binary 2.9.12, itemadapter 0.13.1, SQLAlchemy 2.0.52, pytz 2026.3, w3lib 2.4.1, packaging 26.0, PyMySQL 1.2. Python 3.10+ is required.

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
