Quick Start
===========

Get running in minutes.

1) Install
----------

.. code-block:: bash

   pip install scrapy-ingest

2) Enable (settings.py)
-----------------------

Only the item pipeline is required — requests, logs, stats, parent_url, and error logging turn on automatically:

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   # EITHER a single URL
   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # DB_URL = 'mysql://user:password@localhost:3306/database'
   # OR discrete fields (no URL encoding needed)
   # DB_TYPE = 'mysql'
   # DB_HOST = 'localhost'
   # DB_PORT = 5432
   # DB_USER = 'user'
   # DB_PASSWORD = 'password'
   # DB_NAME = 'database'

   # Optional
   CREATE_TABLES = True
   # JOB_ID = 1  # or omit to auto-generate a unique id
   # INGEST_BATCH_SIZE = 50
   # INGEST_SHOW_SUMMARY = True

3) Run
------

.. code-block:: bash

   scrapy crawl your_spider

4) Verify
---------

Data is written into these tables (created automatically when `CREATE_TABLES = True`):

- `jobs` — per-crawl summary (counts, crawl speed, finish reason, stats); parent of the other tables
- `job_items` — JSON items (with ``crawled_at``)
- `job_requests` — url, parent_url, status, response_time, error, success
- `job_logs` — structured job logs including ``print()``

5) Troubleshooting
------------------

- Password contains `@` or `$`? If using `DB_URL`, encode them (`@` -> `%40`, `$` -> `%24`).
- Or use discrete fields to avoid encoding.
- Yield items from callbacks (not only ``return`` inside a generator).

That's it.
