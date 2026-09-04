Search ingest (Elasticsearch / OpenSearch)
==========================================

``scrapy-ingest`` can index crawl data to Elasticsearch or OpenSearch using ``opensearch-py`` (installed with the package). Both engines use the same REST bulk API, so one client covers both.

Enable Elasticsearch / OpenSearch
---------------------------------

**Elasticsearch / OpenSearch only** — set ``SEARCH_URL`` (no SQL database required):

.. code-block:: python

   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   SEARCH_URL = 'http://localhost:9200'

**Both database and Elasticsearch / OpenSearch:**

.. code-block:: python

   DB_URL = 'postgresql://user:password@localhost:5432/database'
   SEARCH_URL = 'http://localhost:9200'

Authentication
--------------

For clusters that require login:

.. code-block:: python

   SEARCH_URL = 'https://search.example.com:9200'
   SEARCH_USER = 'elastic'
   SEARCH_PASSWORD = 'your-password'
   SEARCH_SSL_VERIFY = True

Indexes created
---------------

By default, documents go into these indexes (prefix ``ingest``):

+----------------------+---------------------------------------------------+
| Index                | Documents                                         |
+======================+===================================================+
| ``ingest-jobs``      | Job status, counts, elapsed time, Scrapy stats    |
+----------------------+---------------------------------------------------+
| ``ingest-job_items`` | Scraped items (JSON)                              |
+----------------------+---------------------------------------------------+
| ``ingest-job_requests`` | Requests with url, fingerprint, parent_url   |
+----------------------+---------------------------------------------------+
| ``ingest-job_logs``  | Log lines (level, logger, message, exception)     |
+----------------------+---------------------------------------------------+

Custom prefix:

.. code-block:: python

   SEARCH_INDEX_PREFIX = 'production'
   # → production-jobs, production-job_items, ...

Verify in Kibana / OpenSearch Dashboards
------------------------------------------

After a crawl, search for documents by ``job_id``:

.. code-block:: text

   GET ingest-jobs/_search
   GET ingest-job_items/_search?q=job_id:Rs_Spider-*

Or use Dev Tools in Kibana:

.. code-block:: json

   GET ingest-job_items/_search
   {
     "query": { "match_all": {} },
     "size": 10
   }

Troubleshooting
---------------

- **Connection refused** — confirm the cluster is running and ``SEARCH_URL`` host/port are correct.
- **401 Unauthorized** — set ``SEARCH_USER`` and ``SEARCH_PASSWORD``.
- **SSL errors** — for self-signed certificates in development, set ``SEARCH_SSL_VERIFY = False``.
- **No indexes** — indexes are created on first flush. Run a spider that yields at least one item or request.
