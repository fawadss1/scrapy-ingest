Scrapy Ingest
===================

|pypi| |pyversions| |downloads| |docs| |license| |changelog|

.. |pypi| image:: https://img.shields.io/pypi/v/scrapy-ingest?color=blue
   :target: https://pypi.org/project/scrapy-ingest/
   :alt: PyPI version
.. |pyversions| image:: https://img.shields.io/pypi/pyversions/scrapy-ingest
   :target: https://pypi.org/project/scrapy-ingest/
   :alt: Python versions
.. |downloads| image:: https://static.pepy.tech/badge/scrapy-ingest
   :target: https://pepy.tech/project/scrapy-ingest
   :alt: Downloads
.. |docs| image:: https://readthedocs.org/projects/scrapy-ingest/badge/?version=latest
   :target: https://scrapy-ingest.readthedocs.io/
   :alt: Documentation
.. |license| image:: https://img.shields.io/badge/license-MIT-green
   :target: https://github.com/fawadss1/scrapy-ingest/blob/master/LICENSE
   :alt: License: MIT
.. |changelog| image:: https://img.shields.io/badge/changelog-releases-informational
   :target: https://github.com/fawadss1/scrapy-ingest/releases
   :alt: Changelog

Save your Scrapy items, requests, logs, and stats to PostgreSQL, MySQL, Elasticsearch, or OpenSearch with a minimal setup.

Quick Start
-----------

1) Install
~~~~~~~~~~

.. code-block:: bash

   pip install scrapy-ingest

2) Enable in settings.py
~~~~~~~~~~~~~~~~~~~~~~~~

Only the item pipeline is required — requests, logs, stats, parent_url, and error logging are enabled automatically:

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   # Destination (default: database only)
   INGEST_TO_DATABASE = True
   INGEST_TO_SEARCH = False

   # Database (when INGEST_TO_DATABASE = True)
   DB_URL = "postgresql://user:password@localhost:5432/database"
   # DB_URL = "mysql://user:password@localhost:3306/database"

   # Search (when INGEST_TO_SEARCH = True)
   # SEARCH_URL = "http://localhost:9200"

   CREATE_TABLES = True

3) Run
~~~~~~

.. code-block:: bash

   scrapy crawl your_spider

Notes
-----

- If your password contains @ or $, URL‑encode them in `DB_URL` (e.g., `PAK@swat1$` -> `PAK%40swat1%24`).
- Or use the discrete fields above to avoid encoding entirely.
- Request ``parent_url`` is the page that scheduled the request. Start URLs are ``null``.
- Logs cover startup → crawl → stats dump → closed (plus ``print()`` spider lines).
- Enable search with ``INGEST_TO_SEARCH = True`` and ``SEARCH_URL``. See :doc:`examples/recipes-search`.

Docs
----
.. toctree::
   :maxdepth: 1

   installation
   quickstart
   configuration
   examples/recipes-search
   examples/recipes-basic
   examples/recipes-items-only
   examples/recipes-requests
   examples/recipes-db-logging
   examples/troubleshooting
   development/changelog

Links
-----

- GitHub: https://github.com/fawadss1/scrapy-ingest
- License: MIT
