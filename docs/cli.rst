Command-line tools
==================

``scrapy-ingest`` installs a CLI alongside the Scrapy extension. Run commands from your Scrapy project directory so Scrapy can load ``settings.py``.

.. code-block:: bash

   scrapy-ingest --help
   scrapy-ingest check-config --help
   scrapy-ingest jobs show --help

check-config
------------

Validate ``DB_URL`` / ``SEARCH_URL`` and ping each configured destination **before** running a spider.

.. code-block:: bash

   scrapy-ingest check-config
   scrapy-ingest check-config --db-url "postgresql://user:pass@localhost:5432/db"
   scrapy-ingest check-config --search-url "http://localhost:9200"

Output:

- A spinner per step while settings load, validation runs, and each destination is pinged
- A summary table on stderr
- Exit code ``0`` when all configured destinations are reachable, ``1`` otherwise

Use this in CI or locally to catch bad credentials, firewall rules, or a stopped Elasticsearch cluster early.

jobs show
---------

Query persisted jobs from SQL (``DB_URL`` / ``DB_*``) or Elasticsearch/OpenSearch (``SEARCH_URL``). When both are configured, SQL is used.

List recent jobs (omit ``job_id``):

.. code-block:: bash

   scrapy-ingest jobs show
   scrapy-ingest jobs show --limit 20
   scrapy-ingest jobs show --status running
   scrapy-ingest jobs show --spider Rs_Spider
   scrapy-ingest jobs show --status finished --spider Rs_Spider

Show one job summary:

.. code-block:: bash

   scrapy-ingest jobs show Rs_Spider-178826754-a1b2
   scrapy-ingest jobs show Rs_Spider-178826754-a1b2 --db-url "postgresql://user:pass@host:5432/db"
   scrapy-ingest jobs show --search-url "http://localhost:9200"

Options:

- ``job_id`` — optional. The string job id (same value as ``JOB_ID`` or the auto-generated id printed in the crawl summary). When omitted, lists recent jobs.
- ``--db-url`` — override ``DB_URL`` from Scrapy settings
- ``--search-url`` — override ``SEARCH_URL`` from Scrapy settings
- ``--limit N`` — max jobs to list when ``job_id`` is omitted (default: ``50``)
- ``--status`` — filter listed jobs by status (list mode only, e.g. ``running``, ``finished``)
- ``--spider`` — filter listed jobs by spider name (list mode only)

Output:

- A spinner while settings load and data is fetched
- **List mode** (no ``job_id``): a table of recent jobs (newest first) with job id, spider, status, timestamps, and counts. Use ``--status`` and/or ``--spider`` to filter.
- **Detail mode** (with ``job_id``): a Field | Value table with all ``jobs`` columns for that crawl

The ``errors`` field counts failed requests plus standalone ERROR/CRITICAL logs (spider callback failures are not double-counted from ``scrapy.core.scraper`` logs).

Exit code ``0`` on success (including an empty job list), ``1`` when a specific job id is not found or the destination cannot be reached.

Example workflow
----------------

.. code-block:: bash

   scrapy-ingest check-config
   scrapy crawl my_spider
   scrapy-ingest jobs show
   scrapy-ingest jobs show my_spider-178826754-a1b2

The job id is printed in the end-of-crawl summary when ``INGEST_SHOW_SUMMARY = True`` (default).
