Basic Recipe: Items + Requests + Logs + Stats
=============================================

The fastest way to store items, requests, Scrapy logs, and crawl stats in PostgreSQL.

1) Install
----------

.. code-block:: bash

   pip install scrapy-ingest

2) Enable (settings.py)
-----------------------

Only the item pipeline is required:

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   # Either one URL
   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # or discrete fields (no URL encoding)
   # DB_HOST = 'localhost'
   # DB_PORT = 5432
   # DB_USER = 'user'
   # DB_PASSWORD = 'password'
   # DB_NAME = 'database'

   CREATE_TABLES = True   # auto-create tables on first run
   # JOB_ID = 1           # optional; unique id generated if omitted

3) Run
------

.. code-block:: bash

   scrapy crawl your_spider

Expected tables
---------------

- ``job_items``: JSON items
- ``job_requests``: requests with parent_url, ``response_time_secs``, error, success
- ``job_logs``: startup → closed, plus ``print()``

Tips
----

- Password contains ``@`` or ``$``? In URLs encode: ``@`` -> ``%40``, ``$`` -> ``%24``.
- Prefer discrete DB fields to avoid encoding entirely.
- Yield items from callbacks (not only ``return`` inside a generator).
