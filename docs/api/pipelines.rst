Pipelines API Reference
=======================

Minimal, auto-generated API docs for pipelines. See README/Quickstart for usage.

.. currentmodule:: scrapy_item_ingest

Main pipelines
--------------

DbInsertPipeline
~~~~~~~~~~~~~~~~

.. autoclass:: DbInsertPipeline
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

.. autoclass:: scrapy_item_ingest.pipelines.base.BasePipeline
   :members:
   :show-inheritance:

Notes
-----
- Tables: `jobs`, `job_items`, `job_requests`, `job_logs` (created when `CREATE_TABLES = True`).
- `DbInsertPipeline` auto-enables requests, logs, stats, parent_url, and error logging.
- Configure DB via `DB_URL` or discrete fields (`DB_HOST`, `DB_USER`, etc.).
- See `configuration` for all settings.
