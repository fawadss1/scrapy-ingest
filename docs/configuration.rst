Configuration
=============

Essential settings for ``settings.py``. See also :doc:`examples/recipes-search` for Elasticsearch / OpenSearch examples.

Pipeline
--------

Only the item pipeline is required. It auto-enables requests, logs, stats, ``parent_url``, and error logging.

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

Ingest destination
------------------

Choose where crawl data is written. **At least one destination must be enabled.**

.. code-block:: python

   # Write ingested data to a relational database (Postgres or MySQL).
   INGEST_TO_DATABASE = True

   # Write ingested data to a search cluster (Elasticsearch or OpenSearch).
   INGEST_TO_SEARCH = False

+------------------+-----------------------------+----------------------------------+
| Mode             | Settings                    | Required                         |
+==================+=============================+==================================+
| Database only    | ``INGEST_TO_DATABASE=True`` | ``DB_URL`` or ``DB_*`` fields    |
| (default)        | ``INGEST_TO_SEARCH=False``  |                                  |
+------------------+-----------------------------+----------------------------------+
| Search only      | ``INGEST_TO_SEARCH=True``   | ``SEARCH_URL``                   |
|                  | ``INGEST_TO_DATABASE=False``|                                  |
+------------------+-----------------------------+----------------------------------+
| Both             | both ``True``               | database + search settings       |
+------------------+-----------------------------+----------------------------------+

When both are enabled, SQL is written first, then search. A search error after a successful SQL commit is logged but does not roll back database rows.

Database settings
-----------------

Required when ``INGEST_TO_DATABASE = True``. Pick **one** connection style.

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

Search settings
---------------

Required when ``INGEST_TO_SEARCH = True``. Connections use ``opensearch-py``, which speaks the same REST bulk API as Elasticsearch and OpenSearch.

**Minimum:**

.. code-block:: python

   INGEST_TO_SEARCH = True
   SEARCH_URL = 'http://localhost:9200'

**With authentication and HTTPS (optional):**

.. code-block:: python

   SEARCH_URL = 'https://search.example.com:9200'
   SEARCH_USER = 'elastic'
   SEARCH_PASSWORD = 'secret'
   SEARCH_SSL_VERIFY = True   # False only for self-signed certs in dev

**Index naming:**

Indexes are named ``{SEARCH_INDEX_PREFIX}-{table}``. Default prefix is ``ingest``:

- ``ingest-jobs``
- ``ingest-job_items``
- ``ingest-job_requests``
- ``ingest-job_logs``

Override the prefix:

.. code-block:: python

   SEARCH_INDEX_PREFIX = 'my_crawl'

The suffix comes from ``JOBS_TABLE``, ``ITEMS_TABLE``, ``REQUESTS_TABLE``, and ``LOGS_TABLE`` (same defaults as SQL table names).

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

SQL table names also define the suffix part of search index names.

.. code-block:: python

   # Defaults
   # ITEMS_TABLE = 'job_items'
   # REQUESTS_TABLE = 'job_requests'
   # LOGS_TABLE = 'job_logs'
   # JOBS_TABLE = 'jobs'

What gets stored
----------------

**Relational database**

- ``jobs`` — per-crawl summary (status, counts, crawl speed, finish reason, stats)
- ``job_items`` — JSON items with ``crawled_at``
- ``job_requests`` — url, ``parent_url``, ``parent_id``, fingerprint, status, ``response_time_secs``, error, success
- ``job_logs`` — time, logger, level, message, exception

**Search cluster**

Same data as JSON documents. Each document includes the string ``job_id``. Search mode stores ``parent_url`` on request documents but does not resolve ``parent_id`` (that linking is SQL-only).

Logging and summary
-------------------

Log level follows Scrapy ``LOG_LEVEL``. Startup logs, Scrapy/Twisted lines, exceptions, and ``print()`` output are stored in ``job_logs`` (or ``ingest-job_logs`` when search is enabled).

When the spider closes, a crawl summary is printed to stderr (independent of ``LOG_LEVEL``) with job id, spider, database URL, search URL, tables/indexes, counts, and elapsed time. Set ``INGEST_SHOW_SUMMARY = False`` to hide it.

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

Tips
----

- Password has ``@`` or ``$``? If using ``DB_URL``, encode them: ``@`` -> ``%40``, ``$`` -> ``%24``.
- Prefer discrete ``DB_*`` fields to avoid URL encoding.
- Request ``parent_url`` is the page that scheduled the request. Start URLs are ``null``.
- Set ``CREATE_TABLES = True`` for the first SQL run, then keep or turn off as you prefer.
- Test search connectivity: ``curl http://localhost:9200``
