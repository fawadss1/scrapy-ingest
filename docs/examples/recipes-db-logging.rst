Recipe: Scrapy logs to DB
=========================

Store full job logs (startup → closed, plus ``print()``) in ``job_logs``.

1) Enable (settings.py)
-----------------------

Logs are included automatically when you use ``DbInsertPipeline``. For logs only:

.. code-block:: python

   EXTENSIONS = {
       'scrapy_ingest.extensions.LoggingExtension': 500,
   }

   # Follows Scrapy LOG_LEVEL (default INFO)
   # LOG_LEVEL = 'INFO'

   # Database
   DB_URL = 'postgresql://user:password@localhost:5432/database'
   # or discrete fields
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

- ``job_logs`` contains startup lines, Scrapy/Twisted messages, exceptions, spider ``print()`` output, and close/stats dump.
- Each row has ``time``, ``level``, ``logger``, ``message``, and ``exception``.

Tips
----

- Keep discrete DB fields if your password has special characters.
- Prefer ``DbInsertPipeline`` so items, requests, and stats are stored too.
