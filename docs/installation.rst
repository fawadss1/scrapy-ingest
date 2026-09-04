Installation
============

Requirements
------------

- Python 3.10+
- Scrapy 2.18+

**Runtime dependencies** (installed automatically):

- ``psycopg2-binary`` — PostgreSQL
- ``PyMySQL`` — MySQL / MariaDB
- ``opensearch-py`` — Elasticsearch / OpenSearch (when ``INGEST_TO_SEARCH = True``)
- ``itemadapter``, ``pytz``, ``w3lib``, ``packaging`` (internal utilities)

Install from PyPI
-----------------

.. code-block:: bash

   pip install scrapy-ingest

Minimal configuration (settings.py)
----------------------------------

Database-only (default):

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   INGEST_TO_DATABASE = True
   INGEST_TO_SEARCH = False

   DB_URL = "postgresql://user:password@localhost:5432/database"

Search-only:

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   INGEST_TO_DATABASE = False
   INGEST_TO_SEARCH = True

   SEARCH_URL = "http://localhost:9200"

Run
---

.. code-block:: bash

   scrapy crawl your_spider

Troubleshooting
---------------

- If your password contains special characters (e.g., ``@``, ``$``) and you use ``DB_URL``, URL-encode them.
  - Example: ``PAK@swat1$`` -> ``PAK%40swat1%24``
- Or use discrete ``DB_*`` fields to avoid URL encoding entirely.
- For search, test connectivity: ``curl http://localhost:9200``

Next steps
----------

- :doc:`quickstart`
- :doc:`configuration`
- :doc:`examples/recipes-search`
- :doc:`examples/troubleshooting`
