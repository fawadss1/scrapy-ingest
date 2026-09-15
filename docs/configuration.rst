Configuration
=============

.. image:: ../static/logo.png
   :align: center
   :width: 520px
   :alt: scrapy-ingest

Essential settings for ``settings.py``. See also :doc:`examples/recipes-search` for Elasticsearch / OpenSearch examples.

Pipeline
--------

Only the item pipeline is required. It auto-enables requests, logs, stats, ``parent_url``, and error logging.

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.IngestPipeline': 300,
   }

Ingest destination
------------------

Set connection URLs to choose where crawl data is written. **At least one is required.**

+------------------+----------------------------+----------------------------------+
| Mode             | Settings                   | Result                           |
+==================+============================+==================================+
| Database only    | ``DB_URL`` or ``DB_*``     | Postgres or MySQL                |
+------------------+----------------------------+----------------------------------+
| Elasticsearch / OpenSearch only | ``SEARCH_URL``             | Elasticsearch or OpenSearch indexes |
+------------------+----------------------------+-------------------------------------+
| Both             | ``DB_URL`` + ``SEARCH_URL``| SQL first, then Elasticsearch/OpenSearch indexes |
+------------------+----------------------------+----------------------------------+

When both are configured, SQL is written first, then Elasticsearch/OpenSearch indexes. An indexing failure after a successful SQL commit is logged but does not roll back database rows.

Database settings
-----------------

Required for SQL ingest. Pick **one** connection style.

**Single URL:**

.. code-block:: python

   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # DB_URL = 'mysql://user:password@localhost:3306/database'

**Discrete fields** (no URL encoding for special characters):

.. code-block:: python

   DB_TYPE = 'postgres'   # or 'mysql' / 'mariadb'
   DB_HOST = 'localhost'
   DB_PORT = 5432         # MySQL: 3306
   DB_USER = 'user'
   DB_PASSWORD = 'password'
   DB_NAME = 'database'

Elasticsearch / OpenSearch settings
-----------------------------------

Set ``SEARCH_URL`` to enable Elasticsearch or OpenSearch ingest. Connections use ``opensearch-py``, which speaks the same REST bulk API as both engines.

**Minimum:**

.. code-block:: python

   SEARCH_URL = 'http://localhost:9200'

**With authentication and HTTPS (optional):**

.. code-block:: python

   SEARCH_URL = 'https://search.example.com:9200'
   SEARCH_USER = 'elastic'
   SEARCH_PASSWORD = 'secret'
   SEARCH_SSL_VERIFY = True   # False only for self-signed certs in dev

**Index naming:**

Elasticsearch/OpenSearch index names match SQL table names by default:

- ``ingest_jobs``
- ``ingest_items``
- ``ingest_requests``
- ``ingest_logs``

Override names with ``JOBS_TABLE``, ``ITEMS_TABLE``, ``REQUESTS_TABLE``, and ``LOGS_TABLE`` (same setting for SQL and search).

Optional settings
-----------------

.. code-block:: python

   CREATE_TABLES = True          # auto-create SQL tables on first run
   # JOB_ID = 1                  # omit to auto-generate a unique id
   INGEST_BATCH_SIZE = 50        # flush when this many rows are buffered
   INGEST_FLUSH_INTERVAL = 10    # periodic flush in seconds
   # INGEST_SHOW_SUMMARY = True  # print crawl summary when the spider closes
   # TIMEZONE = 'Asia/Karachi'

Table and index names
---------------------

The same names are used for SQL tables and Elasticsearch/OpenSearch indexes.

.. code-block:: python

   # Defaults
   # JOBS_TABLE = 'ingest_jobs'
   # ITEMS_TABLE = 'ingest_items'
   # REQUESTS_TABLE = 'ingest_requests'
   # LOGS_TABLE = 'ingest_logs'

What gets stored
----------------

**Relational database**

- ``ingest_jobs`` — per-crawl summary (status, counts, crawl speed, finish reason, stats). ``errors_count`` counts failed requests plus standalone ERROR/CRITICAL logs (not duplicate ``scrapy.core.scraper`` logs for the same request failure).
- ``ingest_items`` — JSON items with ``crawled_at``
- ``ingest_requests`` — url, ``parent_url``, ``parent_id``, fingerprint, status, ``response_time_secs``, error, success. The ``error`` column is set for download failures, HTTP 4xx/5xx (for example ``HTTP 404 Not Found``), and spider callback exceptions (full traceback linked to the request URL).
- ``ingest_logs`` — time, logger, level, message, exception

**Elasticsearch / OpenSearch**

Same data as JSON documents. Each document includes the string ``job_id``. Elasticsearch/OpenSearch mode stores ``parent_url`` on request documents but does not resolve ``parent_id`` (that linking is SQL-only).

Logging and summary
-------------------

Log level follows Scrapy ``LOG_LEVEL``. Startup logs, Scrapy/Twisted lines, exceptions, and ``print()`` output are stored in ``ingest_logs``.

When the spider closes, a crawl summary is printed to stderr (independent of ``LOG_LEVEL``) with job id, spider, database URL, Elasticsearch/OpenSearch URL, tables/indexes, counts, and elapsed time. Set ``INGEST_SHOW_SUMMARY = False`` to hide it.

Update checks
-------------

When a pipeline or extension loads, ``scrapy-ingest`` checks PyPI once per process in a background thread. If a newer version is published, a notice is printed with ``pip install -U scrapy-ingest`` and a release link. Network errors are silent.

Standalone components
---------------------

.. code-block:: python

   # Items only
   ITEM_PIPELINES = {'scrapy_ingest.pipelines.ItemsPipeline': 300}

   # Requests only
   ITEM_PIPELINES = {'scrapy_ingest.pipelines.RequestsPipeline': 300}

   # Logs only
   EXTENSIONS = {'scrapy_ingest.extensions.LoggingExtension': 500}

CLI
---

See :doc:`cli` for full details.

- ``scrapy-ingest check-config`` — validate settings and ping ``DB_URL`` / ``SEARCH_URL`` before crawling
- ``scrapy-ingest jobs show`` — list recent jobs (newest first) from SQL or Elasticsearch/OpenSearch
- ``scrapy-ingest jobs show --status running`` / ``--spider my_spider`` — filter the job list (list mode only)
- ``scrapy-ingest jobs show <job_id>`` — print one job summary as a Field | Value table

When both ``DB_URL`` and ``SEARCH_URL`` are set, ``jobs show`` reads from SQL. Crawls still write to both destinations.

Tips
----

- Run ``scrapy-ingest check-config`` from your Scrapy project to validate ``DB_URL`` / ``SEARCH_URL`` and ping each configured destination before crawling.
- After a crawl, run ``scrapy-ingest jobs show`` (optionally ``--status finished --spider my_spider``) to pick a job id, then ``scrapy-ingest jobs show <job_id>`` for full counts without writing SQL.
- Search-only setup (``SEARCH_URL`` without ``DB_URL``)? ``jobs show`` reads from the ``ingest_jobs`` index (or your customized ``JOBS_TABLE``).
- Password has ``@`` or ``$``? If using ``DB_URL``, encode them: ``@`` -> ``%40``, ``$`` -> ``%24``.
- Prefer discrete ``DB_*`` fields to avoid URL encoding.
- Request ``parent_url`` is the page that scheduled the request. Start URLs are ``null``.
- Set ``CREATE_TABLES = True`` for the first SQL run, then keep or turn off as you prefer.
- Test Elasticsearch/OpenSearch connectivity: ``curl http://localhost:9200``
