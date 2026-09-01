Recipe: Items-only pipeline
==========================

Store only items to PostgreSQL (no request tracking, minimal logging).

1) Enable (settings.py)
-----------------------

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.ItemsPipeline': 300,
   }

   # Database config (pick ONE style)
   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # or discrete fields:
   # DB_HOST = 'localhost'
   # DB_PORT = 5432
   # DB_USER = 'user'
   # DB_PASSWORD = 'password'
   # DB_NAME = 'database'

   CREATE_TABLES = True

2) Run
------

.. code-block:: bash

   scrapy crawl your_spider

Expected
--------

- Items saved as JSON rows in ``job_items`` (each item includes ``crawled_at``).
- No ``job_requests`` / ``job_logs`` / ``jobs`` rows are created in this recipe.

Tip
---

Use discrete DB fields to avoid URL‑encoding special characters in passwords.
