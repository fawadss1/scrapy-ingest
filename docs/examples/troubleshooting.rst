Troubleshooting
===============

This guide covers common issues, error messages, and solutions when using Scrapy Ingest in development and production environments.

Common Installation Issues
--------------------------

PostgreSQL Connection Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``psycopg2.OperationalError: could not connect to server``

**Symptoms:**
- Spider fails to start with database connection error
- Error occurs during pipeline initialization

**Solutions:**

1. **Check PostgreSQL service status:**

   .. code-block:: bash

      # Ubuntu/Debian
      sudo systemctl status postgresql
      sudo systemctl start postgresql

      # macOS with Homebrew
      brew services start postgresql

      # Windows
      net start postgresql-x64-15

2. **Verify database connection string:**

   .. code-block:: python

      # Test connection manually
      import psycopg2

      try:
          conn = psycopg2.connect(
              "postgresql://username:password@localhost:5432/database_name"
          )
          print("✅ Connection successful")
          conn.close()
      except Exception as e:
          print(f"❌ Connection failed: {e}")

3. **Check firewall and network settings:**

   .. code-block:: bash

      # Test port connectivity
      telnet localhost 5432

      # Or using nc
      nc -zv localhost 5432

4. **Verify PostgreSQL configuration:**

   .. code-block:: bash

      # Check postgresql.conf
      sudo nano /etc/postgresql/15/main/postgresql.conf

      # Ensure these settings:
      listen_addresses = '*'  # or 'localhost'
      port = 5432

**Error**: ``psycopg2.OperationalError: FATAL: password authentication failed``

**Solutions:**

1. **Reset PostgreSQL password:**

   .. code-block:: bash

      sudo -u postgres psql
      ALTER USER postgres PASSWORD 'newpassword';

2. **Check pg_hba.conf authentication method:**

   .. code-block:: bash

      sudo nano /etc/postgresql/15/main/pg_hba.conf

      # Change to:
      local   all             all                                     md5
      host    all             all             127.0.0.1/32            md5

3. **Restart PostgreSQL after changes:**

   .. code-block:: bash

      sudo systemctl restart postgresql

Table Creation Issues
~~~~~~~~~~~~~~~~~~~

**Error**: ``relation "job_items" does not exist``

**Symptoms:**
- Spider runs but fails when trying to store items
- Error occurs when `CREATE_TABLES = False`

**Solutions:**

1. **Enable automatic table creation:**

   .. code-block:: python

      # settings.py
      CREATE_TABLES = True

2. **Manually create tables:**

   .. code-block:: sql

      -- Connect to your database and run:
      CREATE TABLE job_items (
          id BIGSERIAL PRIMARY KEY,
          item JSONB NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          job_id INTEGER NOT NULL
      );

      CREATE TABLE job_requests (
          id BIGSERIAL PRIMARY KEY,
          url VARCHAR(200) NOT NULL,
          method VARCHAR(10) NOT NULL,
          status_code INTEGER,
          response_time FLOAT,
          fingerprint VARCHAR(255),
          parent_url VARCHAR(255),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          job_id INTEGER NOT NULL,
          parent_id BIGINT,
          FOREIGN KEY (parent_id) REFERENCES job_requests(id)
      );

      CREATE TABLE job_logs (
          id BIGSERIAL PRIMARY KEY,
          job_id INTEGER NOT NULL,
          type VARCHAR(50) NOT NULL,
          message TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

3. **Check database permissions:**

   .. code-block:: sql

      -- Ensure user has table creation privileges
      GRANT CREATE ON DATABASE your_database TO your_user;
      GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;

Runtime Issues
--------------

Memory-Related Problems
~~~~~~~~~~~~~~~~~~~~~

**Error**: ``MemoryError`` or ``killed`` during crawling

**Symptoms:**
- Spider stops unexpectedly
- High memory usage in system monitor
- Docker container gets killed

**Solutions:**

1. **Enable memory monitoring:**

   .. code-block:: python

      # settings.py
      MEMUSAGE_ENABLED = True
      MEMUSAGE_LIMIT_MB = 2048
      MEMUSAGE_WARNING_MB = 1536

2. **Optimize batch processing:**

   .. code-block:: python

      # Reduce batch sizes
      BATCH_SIZE = 100  # Instead of 1000

      # Process items more frequently
      ITEM_BUFFER_SIZE = 50

3. **Use memory-efficient data structures:**

   .. code-block:: python

      # In your spider
      def parse(self, response):
          # Don't store large objects in memory
          item = {
              'title': response.css('title::text').get(),
              'url': response.url
          }
          # Avoid: item['full_html'] = response.text
          yield item

4. **Configure garbage collection:**

   .. code-block:: python

      # settings.py
      import gc

      # Force garbage collection more frequently
      gc.set_threshold(100, 10, 10)

Performance Issues
~~~~~~~~~~~~~~~~

**Problem**: Slow spider performance or database bottlenecks

**Symptoms:**
- Very slow item processing
- Long response times
- Database connection timeouts

**Solutions:**

1. **Optimize database connections:**

   .. code-block:: python

      # settings.py
      DB_SETTINGS = {
          'pool_size': 20,
          'max_overflow': 30,
          'pool_timeout': 30,
      }

2. **Tune Scrapy concurrency:**

   .. code-block:: python

      # Start with lower values and increase gradually
      CONCURRENT_REQUESTS = 16
      CONCURRENT_REQUESTS_PER_DOMAIN = 8
      DOWNLOAD_DELAY = 0.5

3. **Enable autothrottle:**

   .. code-block:: python

      AUTOTHROTTLE_ENABLED = True
      AUTOTHROTTLE_START_DELAY = 1
      AUTOTHROTTLE_MAX_DELAY = 10
      AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

4. **Optimize database queries:**

   .. code-block:: sql

      -- Add indexes for better performance
      CREATE INDEX CONCURRENTLY idx_job_items_job_id ON job_items(job_id);
      CREATE INDEX CONCURRENTLY idx_job_items_created_at ON job_items(created_at);

Configuration Problems
---------------------

Pipeline Order Issues
~~~~~~~~~~~~~~~~~~~

**Error**: Items not being processed correctly or pipelines not running

**Solutions:**

1. **Check pipeline order:**

   .. code-block:: python

      # Correct order (lower numbers run first)
      ITEM_PIPELINES = {
          'myproject.pipelines.ValidationPipeline': 200,
          'scrapy_ingest.pipelines.DbInsertPipeline': 300,
          'myproject.pipelines.NotificationPipeline': 400,
      }

2. **Ensure pipeline returns items:**

   .. code-block:: python

      def process_item(self, item, spider):
          # Process the item
          processed_item = self.do_processing(item)

          # MUST return the item for next pipeline
          return processed_item

Job ID Configuration Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Items not grouped correctly or job_id is null

**Solutions:**

1. **Explicitly set JOB_ID:**

   .. code-block:: python

      # settings.py
      JOB_ID = 'my_specific_job_001'

2. **Check spider attribute:**

   .. code-block:: python

      # In your spider
      class MySpider(scrapy.Spider):
          name = 'my_spider'

          def __init__(self, job_id=None, *args, **kwargs):
              super().__init__(*args, **kwargs)
              if job_id:
                  self.job_id = job_id

3. **Verify job_id is being set:**

   .. code-block:: python

      # Add logging to check job_id
      def open_spider(self, spider):
          job_id = getattr(spider, 'job_id', spider.name)
          spider.logger.info(f"Using job_id: {job_id}")

Data Quality Issues
------------------

JSON Serialization Errors
~~~~~~~~~~~~~~~~~~~~~~~~

**Error**: ``TypeError: Object of type X is not JSON serializable``

**Solutions:**

1. **Use proper field types:**

   .. code-block:: python

      # Convert datetime objects
      from datetime import datetime

      item['scraped_at'] = datetime.now().isoformat()

      # Convert Decimal to float
      from decimal import Decimal
      price = Decimal('29.99')
      item['price'] = float(price)

2. **Custom serialization:**

   .. code-block:: python

      import json
      from datetime import datetime, date
      from decimal import Decimal

      class CustomJSONEncoder(json.JSONEncoder):
          def default(self, obj):
              if isinstance(obj, (datetime, date)):
                  return obj.isoformat()
              elif isinstance(obj, Decimal):
                  return float(obj)
              return super().default(obj)

3. **Clean data before yielding:**

   .. code-block:: python

      def clean_item(self, item):
          """Clean item data for JSON serialization"""
          cleaned = {}
          for key, value in item.items():
              if isinstance(value, (str, int, float, bool, list, dict)):
                  cleaned[key] = value
              elif value is None:
                  cleaned[key] = None
              else:
                  cleaned[key] = str(value)
          return cleaned

JSONB Query Issues
~~~~~~~~~~~~~~~~

**Problem**: Can't query JSONB fields effectively

**Solutions:**

1. **Use proper JSONB operators:**

   .. code-block:: sql

      -- Extract text values
      SELECT item->>'name' as product_name FROM job_items;

      -- Extract numeric values
      SELECT (item->>'price')::FLOAT as price FROM job_items;

      -- Check for key existence
      SELECT * FROM job_items WHERE item ? 'price';

      -- Query nested objects
      SELECT * FROM job_items WHERE item->'metadata'->>'source' = 'website';

2. **Create functional indexes:**

   .. code-block:: sql

      -- Index for frequently queried fields
      CREATE INDEX idx_items_name ON job_items ((item->>'name'));
      CREATE INDEX idx_items_price ON job_items (((item->>'price')::FLOAT));

Monitoring and Debugging
------------------------

Enable Debug Logging
~~~~~~~~~~~~~~~~~~~

1. **Enable detailed logging:**

   .. code-block:: python

      # settings.py
      LOG_LEVEL = 'DEBUG'

      # Custom logging configuration
      LOGGING = {
          'version': 1,
          'disable_existing_loggers': False,
          'formatters': {
              'verbose': {
                  'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                  'style': '{',
              },
          },
          'handlers': {
              'file': {
                  'level': 'DEBUG',
                  'class': 'logging.FileHandler',
                  'filename': 'scrapy_debug.log',
                  'formatter': 'verbose',
              },
          },
          'loggers': {
              'scrapy_ingest': {
                  'handlers': ['file'],
                  'level': 'DEBUG',
                  'propagate': True,
              },
          },
      }

2. **Add debug information to pipelines:**

   .. code-block:: python

      def process_item(self, item, spider):
          spider.logger.debug(f"Processing item: {item}")
          spider.logger.debug(f"Using job_id: {getattr(spider, 'job_id', 'unknown')}")

          # Process item
          return item

Database Connection Debugging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Test database connectivity:**

   .. code-block:: python

      # test_db.py
      import psycopg2
      import sys

      def test_database_connection(db_url):
          try:
              conn = psycopg2.connect(db_url)
              cursor = conn.cursor()

              # Test basic operations
              cursor.execute("SELECT version();")
              version = cursor.fetchone()[0]
              print(f"✅ Connected to: {version}")

              # Test table access
              cursor.execute("SELECT COUNT(*) FROM job_items;")
              count = cursor.fetchone()[0]
              print(f"✅ Items in database: {count}")

              conn.close()
              return True

          except Exception as e:
              print(f"❌ Database test failed: {e}")
              return False

      if __name__ == "__main__":
          db_url = sys.argv[1] if len(sys.argv) > 1 else "postgresql://user:pass@localhost/db"
          test_database_connection(db_url)

2. **Monitor database connections:**

   .. code-block:: sql

      -- Check active connections
      SELECT
          pid,
          usename,
          application_name,
          client_addr,
          state,
          query_start,
          query
      FROM pg_stat_activity
      WHERE datname = 'your_database_name';

Performance Profiling
~~~~~~~~~~~~~~~~~~~~

1. **Profile spider performance:**

   .. code-block:: python

      # Add profiling to spider
      import cProfile
      import pstats

      class ProfilingSpider(scrapy.Spider):
          def __init__(self, *args, **kwargs):
              super().__init__(*args, **kwargs)
              self.profiler = cProfile.Profile()

          def spider_opened(self, spider):
              self.profiler.enable()

          def spider_closed(self, spider):
              self.profiler.disable()
              stats = pstats.Stats(self.profiler)
              stats.sort_stats('cumulative')
              stats.print_stats(20)  # Top 20 functions

2. **Monitor memory usage:**

   .. code-block:: python

      import psutil
      import os

      class MemoryMonitoringExtension:
          def item_scraped(self, item, response, spider):
              process = psutil.Process(os.getpid())
              memory_mb = process.memory_info().rss / 1024 / 1024
              spider.logger.info(f"Memory usage: {memory_mb:.2f} MB")

Common Error Messages and Solutions
----------------------------------

``ImportError: No module named 'scrapy_ingest'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:**
.. code-block:: bash

   pip install scrapy-ingest
   # Or if developing:
   pip install -e .

``AttributeError: 'Spider' object has no attribute 'job_id'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:**
.. code-block:: python

   # Ensure job_id is set in settings or spider
   JOB_ID = 'your_job_id'
   # Or handle missing job_id gracefully:
   job_id = getattr(spider, 'job_id', spider.name)

``psycopg2.errors.UndefinedTable: relation "job_items" does not exist``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:**
.. code-block:: python

   # Enable table creation
   CREATE_TABLES = True

Getting Help
-----------

When reporting issues, please include:

1. **Environment information:**
   - Python version
   - Scrapy version
   - PostgreSQL version
   - Operating system

2. **Configuration:**
   - Relevant settings.py content
   - Pipeline configuration
   - Database connection string (without credentials)

3. **Error logs:**
   - Complete error traceback
   - Relevant log messages
   - Spider output

4. **Minimal reproduction case:**
   - Simple spider that reproduces the issue
   - Sample data if relevant

**Support Channels:**
- GitHub Issues: https://github.com/fawadss1/scrapy_item_ingest/issues
- Documentation: This documentation site

Next Steps
----------

* :doc:`../api/pipelines` - Detailed API reference
* :doc:`../development/contributing` - Contributing guidelines
* :doc:`../examples/basic-setup` - Basic setup examples
