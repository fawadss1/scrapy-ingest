Utilities API Reference
======================

Minimal, auto-generated docs for utility modules.

Serialization
-------------

.. automodule:: scrapy_ingest.utils.serialization
   :members:

Fingerprint
-----------

.. automodule:: scrapy_ingest.utils.fingerprint
   :members:

Time helpers
------------

.. automodule:: scrapy_ingest.utils.time
   :members:

Console
-------

.. automodule:: scrapy_ingest.utils.console
   :members: info, format_table

Use ``info()`` for user-facing notices (update check, crawl summary). Output
goes to stderr so it stays visible at any ``LOG_LEVEL`` and is not stored in
``job_logs``.

Crawl summary
-------------

.. automodule:: scrapy_ingest.utils.summary
   :members: format_crawl_summary, display_database

Printed automatically when the spider closes, after the ``jobs`` row is finalized.
Set ``INGEST_SHOW_SUMMARY = False`` to hide the tables.

Update checks
-------------

.. automodule:: scrapy_ingest.utils.updates
   :members: update_available, get_update_url, latest_pypi_release, pypi_release_url

When a pipeline or extension loads, ``update_available()`` checks PyPI once per
process in a background thread.

Notes
-----
- These helpers are used by pipelines/extensions; they are safe to import in user code.
- See `quickstart` and `examples` for practical usage.
              'title': 200,
              'description': 1000
          }
      }

      validation_result = validate_item_structure(item, schema)

Custom Serialization Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ItemSerializer
   :members:
   :undoc-members:

   Advanced serialization class with customizable behavior.

   **Methods:**

   .. method:: __init__(options=None)

      Initialize serializer with custom options.

      :param options: Serialization options
      :type options: dict

      **Options:**

      .. code-block:: python

         options = {
             'include_none': False,      # Include None values
             'include_empty': False,     # Include empty strings/lists
             'datetime_format': 'iso',   # 'iso', 'timestamp', or format string
             'decimal_precision': 2,     # Decimal places for numbers
             'max_string_length': 1000,  # Truncate long strings
             'normalize_unicode': True,  # Normalize Unicode strings
         }

   .. method:: serialize(item)

      Serialize item with configured options.

      :param item: Item to serialize
      :returns: Serialized item
      :rtype: dict

   .. method:: add_custom_handler(type_class, handler_func)

      Add custom serialization handler for specific types.

      :param type_class: Type to handle
      :type type_class: type
      :param handler_func: Handler function
      :type handler_func: callable

      **Example:**

      .. code-block:: python

         from dataclasses import dataclass

         @dataclass
         class CustomObject:
             value: str

         serializer = ItemSerializer()
         serializer.add_custom_handler(
             CustomObject,
             lambda obj: {'custom_value': obj.value}
         )

Request Fingerprinting
---------------------

.. automodule:: scrapy_ingest.utils.fingerprint
   :members:
   :undoc-members:

Fingerprint Functions
~~~~~~~~~~~~~~~~~~~

.. autofunction:: request_fingerprint

   Generate unique fingerprint for Scrapy requests.

   :param request: Scrapy request object
   :type request: scrapy.Request
   :param include_headers: Include headers in fingerprint
   :type include_headers: bool
   :returns: Unique request fingerprint
   :rtype: str

   **Algorithm:**

   * Uses SHA1 hash of normalized request data
   * Includes URL, method, and optionally headers
   * Excludes dynamic headers like User-Agent
   * Handles query parameter ordering

   **Example:**

   .. code-block:: python

      import scrapy
      from scrapy_ingest.utils.fingerprint import request_fingerprint

      request1 = scrapy.Request('https://example.com/page?a=1&b=2')
      request2 = scrapy.Request('https://example.com/page?b=2&a=1')

      fp1 = request_fingerprint(request1)
      fp2 = request_fingerprint(request2)
      # fp1 == fp2 (same fingerprint for equivalent requests)

.. autofunction:: normalize_url

   Normalize URL for consistent fingerprinting.

   :param url: URL to normalize
   :type url: str
   :returns: Normalized URL
   :rtype: str

   **Normalization Steps:**

   * Converts to lowercase
   * Sorts query parameters
   * Removes fragment identifiers
   * Handles URL encoding consistently
   * Removes default ports

.. autofunction:: url_fingerprint

   Generate fingerprint for URL only (without method/headers).

   :param url: URL to fingerprint
   :type url: str
   :returns: URL fingerprint
   :rtype: str

Database Utilities
-----------------

.. automodule:: scrapy_ingest.utils.database
   :members:
   :undoc-members:

Connection Utilities
~~~~~~~~~~~~~~~~~~

.. autofunction:: test_connection

   Test database connection and return status.

   :param db_url: Database connection string
   :type db_url: str
   :returns: Connection test results
   :rtype: dict

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.database import test_connection

      result = test_connection('postgresql://user:pass@localhost:5432/db')
      # Result: {'connected': True, 'version': '15.3', 'latency': 0.023}

.. autofunction:: get_table_info

   Get information about database tables.

   :param connection: Database connection
   :type connection: psycopg2.connection
   :param table_name: Name of table to inspect
   :type table_name: str
   :returns: Table information
   :rtype: dict

.. autofunction:: execute_with_retry

   Execute database operation with automatic retry logic.

   :param connection: Database connection
   :param query: SQL query to execute
   :param params: Query parameters
   :param max_retries: Maximum retry attempts
   :returns: Query results
   :raises: DatabaseError if all retries fail

Query Builders
~~~~~~~~~~~~~

.. autoclass:: QueryBuilder
   :members:
   :undoc-members:

   Helper class for building database queries dynamically.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.database import QueryBuilder

      builder = QueryBuilder('job_items')
      query = (builder
               .select(['item', 'created_at'])
               .where('job_id = %s')
               .where('created_at > %s')
               .order_by('created_at DESC')
               .limit(100)
               .build())

.. autoclass:: BatchInserter
   :members:
   :undoc-members:

   Optimized batch insertion utility for high-performance scenarios.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.database import BatchInserter

      inserter = BatchInserter(connection, 'job_items', batch_size=1000)

      for item in items:
          inserter.add_item({
              'item': json.dumps(item),
              'job_id': job_id,
              'created_at': datetime.now()
          })

      inserter.flush()  # Insert remaining items

Data Processing
--------------

.. automodule:: scrapy_ingest.utils.processing
   :members:
   :undoc-members:

Data Cleaning
~~~~~~~~~~~~

.. autofunction:: clean_text

   Clean and normalize text data.

   :param text: Text to clean
   :type text: str
   :param options: Cleaning options
   :type options: dict
   :returns: Cleaned text
   :rtype: str

   **Cleaning Options:**

   .. code-block:: python

      options = {
          'strip_whitespace': True,    # Remove leading/trailing whitespace
          'normalize_spaces': True,    # Normalize multiple spaces to single
          'remove_empty_lines': True,  # Remove empty lines
          'normalize_unicode': True,   # Normalize Unicode characters
          'remove_html': False,        # Strip HTML tags
          'max_length': None,          # Maximum text length
      }

.. autofunction:: extract_numbers

   Extract numeric values from text.

   :param text: Text containing numbers
   :type text: str
   :param number_type: Type of numbers to extract
   :type number_type: str
   :returns: Extracted numbers
   :rtype: list

   **Example:**

   .. code-block:: python

      price_text = "Regular price: $29.99 (was $39.99)"
      numbers = extract_numbers(price_text, 'float')
      # Result: [29.99, 39.99]

.. autofunction:: normalize_currency

   Normalize currency values to standard format.

   :param currency_text: Text containing currency
   :type currency_text: str
   :param target_currency: Target currency code
   :type target_currency: str
   :returns: Normalized currency value
   :rtype: dict

Data Validation
~~~~~~~~~~~~~~

.. autoclass:: DataValidator
   :members:
   :undoc-members:

   Comprehensive data validation utility.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.processing import DataValidator

      validator = DataValidator()

      # Add validation rules
      validator.add_rule('email', r'^[^@]+@[^@]+\.[^@]+$')
      validator.add_rule('url', validator.is_valid_url)
      validator.add_rule('phone', validator.is_valid_phone)

      # Validate data
      data = {
          'email': 'user@example.com',
          'website': 'https://example.com',
          'phone': '+1-555-123-4567'
      }

      is_valid, errors = validator.validate(data)

Caching Utilities
----------------

.. automodule:: scrapy_ingest.utils.cache
   :members:
   :undoc-members:

Redis Cache
~~~~~~~~~~

.. autoclass:: RedisCache
   :members:
   :undoc-members:

   Redis-based caching utility for scraped data.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.cache import RedisCache

      cache = RedisCache('redis://localhost:6379/0')

      # Cache item
      cache.set('item:123', item_data, ttl=3600)

      # Retrieve item
      cached_item = cache.get('item:123')

      # Check if exists
      if cache.exists('item:123'):
          print("Item found in cache")

Memory Cache
~~~~~~~~~~~

.. autoclass:: MemoryCache
   :members:
   :undoc-members:

   In-memory caching for temporary data storage.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.cache import MemoryCache

      cache = MemoryCache(max_size=1000)
      cache.set('key', 'value', ttl=300)
      value = cache.get('key')

Monitoring Utilities
-------------------

.. automodule:: scrapy_ingest.utils.monitoring
   :members:
   :undoc-members:

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PerformanceMonitor
   :members:
   :undoc-members:

   Monitor spider performance metrics.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.monitoring import PerformanceMonitor

      monitor = PerformanceMonitor()

      # Start monitoring
      monitor.start_timer('page_processing')

      # ... process page ...

      # Stop and record
      elapsed = monitor.stop_timer('page_processing')
      monitor.record_metric('items_processed', 1)

      # Get statistics
      stats = monitor.get_statistics()

Health Checks
~~~~~~~~~~~~

.. autofunction:: check_database_health

   Perform comprehensive database health check.

   :param db_url: Database connection string
   :returns: Health check results
   :rtype: dict

.. autofunction:: check_redis_health

   Check Redis connection and performance.

   :param redis_url: Redis connection string
   :returns: Health check results
   :rtype: dict

Configuration Helpers
---------------------

.. automodule:: scrapy_ingest.utils.config
   :members:
   :undoc-members:

Environment Utilities
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: load_env_file

   Load environment variables from .env file.

   :param file_path: Path to .env file
   :type file_path: str
   :returns: Loaded environment variables
   :rtype: dict

.. autofunction:: get_env_with_fallback

   Get environment variable with multiple fallback options.

   :param keys: List of environment variable names to try
   :type keys: list
   :param default: Default value if none found
   :returns: Environment variable value
   :rtype: str

   **Example:**

   .. code-block:: python

      # Try multiple environment variable names
      db_url = get_env_with_fallback([
          'DATABASE_URL',
          'SCRAPY_DB_URL',
          'DB_CONNECTION_STRING'
      ], default='postgresql://localhost:5432/scrapy')

Testing Utilities
----------------

.. automodule:: scrapy_ingest.utils.testing
   :members:
   :undoc-members:

Test Data Generation
~~~~~~~~~~~~~~~~~~

.. autofunction:: generate_test_items

   Generate test items for pipeline testing.

   :param count: Number of items to generate
   :type count: int
   :param item_type: Type of items to generate
   :type item_type: str
   :returns: List of test items
   :rtype: list

.. autofunction:: create_test_spider

   Create mock spider for testing.

   :param name: Spider name
   :type name: str
   :param settings: Spider settings
   :type settings: dict
   :returns: Mock spider instance
   :rtype: Mock

Database Testing
~~~~~~~~~~~~~~~

.. autoclass:: TestDatabaseManager
   :members:
   :undoc-members:

   Manage test databases for unit testing.

   **Example:**

   .. code-block:: python

      from scrapy_ingest.utils.testing import TestDatabaseManager

      # In test setup
      db_manager = TestDatabaseManager()
      test_db_url = db_manager.create_test_database()

      # Run tests with test database

      # In test teardown
      db_manager.cleanup_test_database()

See Also
--------

* :doc:`pipelines` - Pipeline API reference
* :doc:`extensions` - Extensions API reference
* :doc:`../user-guide/advanced-usage` - Advanced usage patterns
