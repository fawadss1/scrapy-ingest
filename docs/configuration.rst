Configuration
=============

Essential settings only. Add these to your Scrapy project's settings.py.

Required
--------

- Database (pick ONE style)

.. code-block:: python

   # Single URL
   DB_URL = 'postgresql://user:password@localhost:5432/database'

   # OR discrete fields (no URL encoding needed)
   # DB_TYPE = 'postgres'
   # DB_HOST = 'localhost'
   # DB_PORT = 5432
   # DB_USER = 'user'
   # DB_PASSWORD = 'password'
   # DB_NAME = 'database'

Recommended
-----------

Only the item pipeline is required. It auto-enables requests, logs, stats, parent_url, and error logging.

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

Optional
--------

.. code-block:: python

   # DB_TYPE = 'postgres'        # used with discrete DB_* fields
   CREATE_TABLES = True          # auto-create tables on first run
   # JOB_ID = 1                  # omit to auto-generate a unique id
   INGEST_BATCH_SIZE = 50        # flush when this many rows are buffered
   INGEST_FLUSH_INTERVAL = 10    # periodic flush in seconds
   # TIMEZONE = 'Asia/Karachi'

Table names (optional)
----------------------

.. code-block:: python

   # Defaults
   # ITEMS_TABLE = 'job_items'
   # REQUESTS_TABLE = 'job_requests'
   # LOGS_TABLE = 'job_logs'
   # JOBS_TABLE = 'jobs'

Logging
-------

Log level follows Scrapy ``LOG_LEVEL``. Startup logs, Scrapy/Twisted lines, exceptions, and ``print()`` output are stored in ``job_logs``.

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

- Password has `@` or `$`? If using `DB_URL`, encode them: `@` -> `%40`, `$` -> `%24`.
- Prefer discrete fields to avoid URL encoding.
- Request ``parent_url`` is the page that scheduled the request. Start URLs are ``null``.
- Set `CREATE_TABLES = True` for the first run, then keep or turn off as you prefer.
