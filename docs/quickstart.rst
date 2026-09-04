Quick Start
===========

Get running in minutes.

1) Install
----------

.. code-block:: bash

   pip install scrapy-ingest

2) Enable (settings.py)
-----------------------

Only the item pipeline is required — requests, logs, stats, ``parent_url``, and error logging turn on automatically.

**Database only**

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # DB_URL = 'mysql://user:password@localhost:3306/database'

   CREATE_TABLES = True

**Elasticsearch / OpenSearch only**

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   SEARCH_URL = 'http://localhost:9200'

**Both**

.. code-block:: python

   DB_URL = 'postgresql://user:password@localhost:5432/database'
   SEARCH_URL = 'http://localhost:9200'

3) Run
------

.. code-block:: bash

   scrapy crawl your_spider

4) Verify
---------

**Database** — tables created when ``CREATE_TABLES = True``:

- ``jobs`` — per-crawl summary (counts, crawl speed, finish reason, stats)
- ``job_items`` — JSON items (with ``crawled_at``)
- ``job_requests`` — url, ``parent_url``, status, ``response_time_secs``, error, success
- ``job_logs`` — structured job logs including ``print()``

**Elasticsearch / OpenSearch** — indexes created on first flush (default prefix ``ingest``):

- ``ingest-jobs``, ``ingest-job_items``, ``ingest-job_requests``, ``ingest-job_logs``

When the spider closes, a crawl summary is printed to stderr with job id, destinations, counts, and elapsed time.

5) Troubleshooting
------------------

- Password contains ``@`` or ``$``? If using ``DB_URL``, encode them (``@`` -> ``%40``, ``$`` -> ``%24``).
- Or use discrete ``DB_*`` fields to avoid encoding.
- Yield items from callbacks (not only ``return`` inside a generator).
- Elasticsearch / OpenSearch not connecting? Check ``SEARCH_URL`` and run ``curl http://localhost:9200``.

That's it. See :doc:`configuration` and :doc:`examples/recipes-search` for full options.
