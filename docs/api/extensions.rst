Extensions API Reference
=======================

Minimal, auto-generated API docs for extensions.

.. currentmodule:: scrapy_ingest

LoggingExtension
----------------

.. autoclass:: LoggingExtension
   :members:
   :show-inheritance:

StatsExtension
--------------

.. autoclass:: StatsExtension
   :members:
   :show-inheritance:

Notes
-----
- `LoggingExtension` persists full job logs (startup → closed, plus ``print()``) to `job_logs`.
- `StatsExtension` stores Scrapy crawl stats on `jobs.stats` when the spider closes.
- Both are auto-enabled by `DbInsertPipeline`. Log level follows Scrapy ``LOG_LEVEL``.
- See `configuration` for settings and Quickstart/Examples for usage.

      Called when an item is dropped by a pipeline.

      :param item: The dropped item
      :type item: dict or scrapy.Item
      :param response: The response from which the item was scraped
      :type response: scrapy.Response
      :param exception: The exception that caused the drop
      :type exception: Exception
      :param spider: The spider instance
      :type spider: scrapy.Spider

Base Extension Class
-------------------

BaseExtension
~~~~~~~~~~~~

.. autoclass:: scrapy_ingest.extensions.base.BaseExtension
   :members:
   :undoc-members:
   :show-inheritance:

   Base class for all extensions. Provides common functionality for database operations and logging.

   **Methods:**

   .. method:: from_crawler(cls, crawler)

      Create extension instance from crawler. Class method used by Scrapy.

      :param crawler: The crawler instance
      :type crawler: scrapy.crawler.Crawler
      :returns: Extension instance
      :rtype: BaseExtension

   .. method:: get_database_connection()

      Get database connection for logging operations.

      :returns: Database connection
      :rtype: psycopg2.connection

   .. method:: log_message(spider, log_type, message)

      Store log message in database.

      :param spider: The spider instance
      :type spider: scrapy.Spider
      :param log_type: Type of log message (INFO, ERROR, WARNING, etc.)
      :type log_type: str
      :param message: Log message content
      :type message: str

   .. method:: get_job_id(spider)

      Get job ID from spider or settings.

      :param spider: The spider instance
      :type spider: scrapy.Spider
      :returns: Job identifier
      :rtype: str or int

Custom Extension Development
---------------------------

Creating Custom Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~

You can create custom extensions by inheriting from ``BaseExtension``:

.. code-block:: python

   from scrapy_ingest.extensions.base import BaseExtension
   from scrapy import signals
   import time

   class PerformanceMonitoringExtension(BaseExtension):
       """Custom extension for monitoring spider performance"""

       def __init__(self, settings):
           super().__init__(settings)
           self.start_time = None
           self.item_count = 0
           self.error_count = 0

       @classmethod
       def from_crawler(cls, crawler):
           ext = cls(crawler.settings)

           # Connect to Scrapy signals
           crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
           crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
           crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
           crawler.signals.connect(ext.spider_error, signal=signals.spider_error)

           return ext

       def spider_opened(self, spider):
           self.start_time = time.time()
           self.log_message(spider, 'INFO', f'Performance monitoring started for {spider.name}')

       def spider_closed(self, spider):
           duration = time.time() - self.start_time
           rate = self.item_count / duration if duration > 0 else 0

           message = (f'Spider {spider.name} performance summary: '
                     f'Items: {self.item_count}, '
                     f'Errors: {self.error_count}, '
                     f'Duration: {duration:.2f}s, '
                     f'Rate: {rate:.2f} items/sec')

           self.log_message(spider, 'INFO', message)

       def item_scraped(self, item, response, spider):
           self.item_count += 1

           # Log milestone progress
           if self.item_count % 1000 == 0:
               elapsed = time.time() - self.start_time
               rate = self.item_count / elapsed
               message = f'Progress: {self.item_count} items scraped, rate: {rate:.2f} items/sec'
               self.log_message(spider, 'INFO', message)

       def spider_error(self, failure, response, spider):
           self.error_count += 1
           self.log_message(spider, 'ERROR', f'Spider error #{self.error_count}: {failure.value}')

Signal Handling
~~~~~~~~~~~~~~

Extensions can connect to various Scrapy signals:

.. code-block:: python

   from scrapy import signals

   class SignalHandlingExtension(BaseExtension):
       @classmethod
       def from_crawler(cls, crawler):
           ext = cls(crawler.settings)

           # Spider signals
           crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
           crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
           crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
           crawler.signals.connect(ext.spider_error, signal=signals.spider_error)

           # Item signals
           crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
           crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)

           # Request/Response signals
           crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
           crawler.signals.connect(ext.response_received, signal=signals.response_received)
           crawler.signals.connect(ext.request_dropped, signal=signals.request_dropped)

           return ext

Extension Configuration
----------------------

Settings and Parameters
~~~~~~~~~~~~~~~~~~~~~~

Extensions can be configured through Scrapy settings:

.. code-block:: python

   class ConfigurableExtension(BaseExtension):
       def __init__(self, settings):
           super().__init__(settings)

           # Read custom settings
           self.monitoring_interval = settings.getint('MONITORING_INTERVAL', 60)
           self.alert_threshold = settings.getfloat('ERROR_THRESHOLD', 0.05)
           self.notification_url = settings.get('NOTIFICATION_WEBHOOK_URL')

           # Validate configuration
           if self.monitoring_interval < 10:
               raise ValueError("MONITORING_INTERVAL must be at least 10 seconds")

   # In settings.py
   EXTENSIONS = {
       'myproject.extensions.ConfigurableExtension': 500,
   }

   # Extension settings
   MONITORING_INTERVAL = 120  # 2 minutes
   ERROR_THRESHOLD = 0.10     # 10% error rate
   NOTIFICATION_WEBHOOK_URL = 'https://hooks.slack.com/...'

Integration Examples
-------------------

Webhook Notifications
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import requests
   import json
   from datetime import datetime

   class WebhookNotificationExtension(BaseExtension):
       def __init__(self, settings):
           super().__init__(settings)
           self.webhook_url = settings.get('WEBHOOK_URL')
           self.notification_interval = settings.getint('NOTIFICATION_INTERVAL', 1000)
           self.item_count = 0

       def item_scraped(self, item, response, spider):
           self.item_count += 1

           if self.item_count % self.notification_interval == 0:
               self.send_progress_notification(spider)

       def spider_closed(self, spider):
           self.send_completion_notification(spider)

       def send_progress_notification(self, spider):
           if not self.webhook_url:
               return

           payload = {
               'type': 'progress',
               'spider': spider.name,
               'items_scraped': self.item_count,
               'timestamp': datetime.now().isoformat()
           }

           try:
               response = requests.post(self.webhook_url, json=payload, timeout=5)
               response.raise_for_status()
               self.log_message(spider, 'INFO', f'Progress notification sent: {self.item_count} items')
           except Exception as e:
               self.log_message(spider, 'WARNING', f'Webhook notification failed: {e}')

       def send_completion_notification(self, spider):
           if not self.webhook_url:
               return

           stats = spider.crawler.stats.get_stats()
           payload = {
               'type': 'completed',
               'spider': spider.name,
               'final_stats': {
                   'items_scraped': stats.get('item_scraped_count', 0),
                   'requests_count': stats.get('downloader/request_count', 0),
                   'duration': stats.get('elapsed_time_seconds', 0),
               },
               'timestamp': datetime.now().isoformat()
           }

           try:
               response = requests.post(self.webhook_url, json=payload, timeout=5)
               response.raise_for_status()
               self.log_message(spider, 'INFO', 'Completion notification sent')
           except Exception as e:
               self.log_message(spider, 'WARNING', f'Completion notification failed: {e}')

Metrics Collection
~~~~~~~~~~~~~~~~

.. code-block:: python

   from prometheus_client import Counter, Gauge, Histogram, start_http_server

   class PrometheusMetricsExtension(BaseExtension):
       def __init__(self, settings):
           super().__init__(settings)

           # Prometheus metrics
           self.items_total = Counter('scrapy_items_scraped_total', 'Total items scraped', ['spider'])
           self.requests_total = Counter('scrapy_requests_total', 'Total requests made', ['spider', 'status'])
           self.response_time = Histogram('scrapy_response_time_seconds', 'Response time', ['spider'])
           self.active_spiders = Gauge('scrapy_active_spiders', 'Number of active spiders')

           # Start metrics server
           metrics_port = settings.getint('PROMETHEUS_PORT', 8000)
           start_http_server(metrics_port)

       def item_scraped(self, item, response, spider):
           self.items_total.labels(spider=spider.name).inc()

       def response_received(self, response, request, spider):
           self.requests_total.labels(
               spider=spider.name,
               status=response.status
           ).inc()

           # Calculate response time
           if hasattr(request, 'meta') and 'download_slot' in request.meta:
               response_time = getattr(response, 'download_latency', 0)
               self.response_time.labels(spider=spider.name).observe(response_time)

       def spider_opened(self, spider):
           self.active_spiders.inc()

       def spider_closed(self, spider):
           self.active_spiders.dec()

Testing Extensions
-----------------

Unit Testing
~~~~~~~~~~~

.. code-block:: python

   import unittest
   from unittest.mock import Mock, patch
   from scrapy_ingest.extensions.logging import LoggingExtension

   class TestLoggingExtension(unittest.TestCase):
       def setUp(self):
           self.settings = Mock()
           self.settings.get.return_value = 'postgresql://test:test@localhost/test'
           self.extension = LoggingExtension(self.settings)

       def test_spider_opened_logs_event(self):
           spider = Mock()
           spider.name = 'test_spider'

           with patch.object(self.extension, 'log_message') as mock_log:
               self.extension.spider_opened(spider)
               mock_log.assert_called_once()

               # Verify log message
               call_args = mock_log.call_args[0]
               self.assertEqual(call_args[1], 'INFO')
               self.assertIn('Spider opened', call_args[2])

       def test_error_logging(self):
           spider = Mock()
           failure = Mock()
           failure.value = Exception("Test error")

           with patch.object(self.extension, 'log_message') as mock_log:
               self.extension.spider_error(failure, None, spider)
               mock_log.assert_called_once_with(spider, 'ERROR', 'Spider error: Test error')

Integration Testing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scrapy.utils.test import get_crawler
   from scrapy_ingest.extensions.logging import LoggingExtension

   def test_extension_integration():
       # Create test crawler
       crawler = get_crawler(spidercls=None, settings_dict={
           'EXTENSIONS': {
               'scrapy_ingest.extensions.LoggingExtension': 500,
           },
           'DB_URL': 'postgresql://test:test@localhost/test_db'
       })

       # Get extension instance
       extension = LoggingExtension.from_crawler(crawler)

       # Test extension functionality
       spider = Mock()
       spider.name = 'test_spider'

       extension.spider_opened(spider)
       # Verify database logging occurred

Error Handling
-------------

Exception Handling in Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class RobustExtension(BaseExtension):
       def spider_error(self, failure, response, spider):
           try:
               # Log the error
               error_msg = f"Spider error: {failure.value}"
               self.log_message(spider, 'ERROR', error_msg)

               # Additional error processing
               self.handle_error_notification(spider, failure)

           except Exception as e:
               # Fallback logging if database fails
               spider.logger.error(f"Extension error handling failed: {e}")

       def handle_error_notification(self, spider, failure):
           """Handle error notifications with proper exception handling"""
