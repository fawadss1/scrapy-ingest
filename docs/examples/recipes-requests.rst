Recipe: Requests tracking
=========================

Track requests with parent_url, response time, and download errors.

1) Enable (settings.py)
-----------------------

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.RequestsPipeline': 300,
   }

   # Database
   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # or discrete fields
   # DB_HOST = 'localhost'
   # DB_PORT = 5432
   # DB_USER = 'user'
   # DB_PASSWORD = 'password'
   # DB_NAME = 'database'

   CREATE_TABLES = True

2) What it logs
---------------

- URL, method
- ``parent_url`` / ``parent_id`` — the page that scheduled the request (start URLs are ``null``)
- status_code
- response_time (seconds)
- fingerprint
- ``error`` / ``success`` — failed downloads include the exception message

3) Run
------

.. code-block:: bash

   scrapy crawl your_spider

Expected
--------

- Rows in ``job_requests`` with ``parent_url`` and ``parent_id`` filled when the request was yielded from a response callback.
- Items table untouched in this recipe (no ItemsPipeline).

Tip
---

Prefer ``DbInsertPipeline`` if you also want items, logs, and stats. It enables this automatically.
