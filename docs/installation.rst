Installation
============

Requirements
------------

- Python 3.10+
- Scrapy
- PostgreSQL or MySQL

Install from PyPI
-----------------

.. code-block:: bash

   pip install scrapy-ingest

Minimal configuration (settings.py)
----------------------------------

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   # Pick ONE of the two database config styles:
   DB_URL = "postgresql://user:password@localhost:5432/database"
   # DB_URL = "mysql://user:password@localhost:3306/database"
   # Or use discrete fields (no URL encoding needed):
   # DB_TYPE = "postgres"   # or "mysql"
   # DB_HOST = "localhost"
   # DB_PORT = 5432
   # DB_USER = "user"
   # DB_PASSWORD = "password"
   # DB_NAME = "database"

   # Optional
   CREATE_TABLES = True
   # JOB_ID = 1  # or omit to auto-generate a unique id

Run
---

.. code-block:: bash

   scrapy crawl your_spider

Troubleshooting
---------------

- If your password contains special characters (e.g., `@`, `$`) and you use `DB_URL`, URL‑encode them.
  - Example: `PAK@swat1$` -> `PAK%40swat1%24`
- Or use the discrete fields to avoid URL encoding entirely.

Next steps
----------

- :doc:`quickstart`
- :doc:`configuration`
- :doc:`examples/troubleshooting`
