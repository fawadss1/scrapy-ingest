Changelog
=========

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
