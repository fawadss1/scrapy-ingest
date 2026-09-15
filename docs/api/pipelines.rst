Pipelines API Reference
=======================

Minimal, auto-generated API docs for pipelines. See README/Quickstart for usage.

.. currentmodule:: scrapy_ingest

Main pipelines
--------------

IngestPipeline
~~~~~~~~~~~~~~

.. autoclass:: IngestPipeline
   :members:
   :show-inheritance:

ItemsPipeline
~~~~~~~~~~~~~

.. autoclass:: ItemsPipeline
   :members:
   :show-inheritance:

RequestsPipeline
~~~~~~~~~~~~~~~~

.. autoclass:: RequestsPipeline
   :members:
   :show-inheritance:

Base class
----------

.. autoclass:: scrapy_ingest.pipelines.base.BasePipeline
   :members:
   :show-inheritance:

Notes
-----
- Tables: `ingest_jobs`, `ingest_items`, `ingest_requests`, `ingest_logs` (created when `CREATE_TABLES = True`).
- `IngestPipeline` auto-enables requests, logs, stats, parent_url, and error logging.
- Configure SQL via `DB_URL` or discrete fields; configure search via `SEARCH_URL`.
- See `configuration` for all settings.
