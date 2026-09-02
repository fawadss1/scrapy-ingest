Advanced Configurations
======================

This section covers complex configuration scenarios and advanced usage patterns for Scrapy Ingest in enterprise and high-performance environments.

Multi-Environment Setup
-----------------------

Production-Grade Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A complete multi-environment setup with proper configuration management:

.. code-block:: python

   # config/base.py - Base configuration
   import os
   from pathlib import Path

   class BaseConfig:
       # Project settings
       BOT_NAME = 'enterprise_scraper'
       SPIDER_MODULES = ['enterprise_scraper.spiders']
       NEWSPIDER_MODULE = 'enterprise_scraper.spiders'

       # Default Scrapy settings
       ROBOTSTXT_OBEY = True
       USER_AGENT = 'enterprise_scraper (+https://yourcompany.com)'

       # Database settings (will be overridden by environment)
       CREATE_TABLES = False

       # Pipeline configuration
       ITEM_PIPELINES = {
           'enterprise_scraper.pipelines.ValidationPipeline': 200,
           'scrapy_ingest.pipelines.DbInsertPipeline': 300,
           'enterprise_scraper.pipelines.NotificationPipeline': 400,
       }

       # Extensions
       EXTENSIONS = {
           'scrapy_ingest.extensions.LoggingExtension': 500,
           'enterprise_scraper.extensions.MetricsExtension': 510,
       }

.. code-block:: python

   # config/development.py - Development environment
   from .base import BaseConfig

   class DevelopmentConfig(BaseConfig):
       # Database
       DB_URL = 'postgresql://dev_user:dev_pass@localhost:5432/scrapy_dev'
       CREATE_TABLES = True

       # Performance settings for development
       CONCURRENT_REQUESTS = 8
       DOWNLOAD_DELAY = 1
       RANDOMIZE_DOWNLOAD_DELAY = 0.5

       # Logging
       LOG_LEVEL = 'DEBUG'

       # Limit items for testing
       CLOSESPIDER_ITEMCOUNT = 100

.. code-block:: python

   # config/staging.py - Staging environment
   from .base import BaseConfig
   import os

   class StagingConfig(BaseConfig):
       # Database
       DB_URL = os.getenv('STAGING_DATABASE_URL')
       CREATE_TABLES = True

       # Performance settings
       CONCURRENT_REQUESTS = 16
       CONCURRENT_REQUESTS_PER_DOMAIN = 8
       DOWNLOAD_DELAY = 0.5

       # Autothrottle for staging
       AUTOTHROTTLE_ENABLED = True
       AUTOTHROTTLE_START_DELAY = 1
       AUTOTHROTTLE_MAX_DELAY = 10
       AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0

       # Logging
       LOG_LEVEL = 'INFO'

.. code-block:: python

   # config/production.py - Production environment
   from .base import BaseConfig
   import os

   class ProductionConfig(BaseConfig):
       # Database (from environment variables)
       DB_URL = os.getenv('DATABASE_URL')
       CREATE_TABLES = False  # Tables must exist in production

       # High-performance settings
       CONCURRENT_REQUESTS = 32
       CONCURRENT_REQUESTS_PER_DOMAIN = 16
       DOWNLOAD_DELAY = 0.1

       # Advanced autothrottle
       AUTOTHROTTLE_ENABLED = True
       AUTOTHROTTLE_START_DELAY = 0.1
       AUTOTHROTTLE_MAX_DELAY = 5
       AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0
       AUTOTHROTTLE_DEBUG = False

       # Production logging
       LOG_LEVEL = 'WARNING'
       TELNETCONSOLE_ENABLED = False

       # Database connection pooling
       DB_SETTINGS = {
           'pool_size': 20,
           'max_overflow': 30,
           'pool_timeout': 30,
           'pool_recycle': 3600,
           'pool_pre_ping': True,
       }

Environment Loader
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings.py - Dynamic environment loading
   import os
   from importlib import import_module

   def get_config():
       env = os.getenv('SCRAPY_ENV', 'development')
       config_map = {
           'development': 'config.development.DevelopmentConfig',
           'staging': 'config.staging.StagingConfig',
           'production': 'config.production.ProductionConfig',
       }

       config_path = config_map.get(env)
       if not config_path:
           raise ValueError(f"Unknown environment: {env}")

       module_path, class_name = config_path.rsplit('.', 1)
       module = import_module(module_path)
       return getattr(module, class_name)

   # Load configuration based on environment
   config = get_config()

   # Apply all settings from config class
   for setting in dir(config):
       if setting.isupper():
           globals()[setting] = getattr(config, setting)

Running with Different Environments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Development
   SCRAPY_ENV=development scrapy crawl products

   # Staging
   SCRAPY_ENV=staging scrapy crawl products

   # Production
   SCRAPY_ENV=production scrapy crawl products

Distributed Crawling Architecture
---------------------------------

Redis-Based Job Queue System
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # distributors/job_manager.py
   import redis
   import json
   import uuid
   from datetime import datetime

   class DistributedJobManager:
       def __init__(self, redis_url='redis://localhost:6379'):
           self.redis = redis.from_url(redis_url)
           self.jobs_queue = 'scrapy:jobs'
           self.results_queue = 'scrapy:results'

       def create_crawl_job(self, spider_name, urls, config=None):
           """Create a distributed crawl job"""
           job_id = str(uuid.uuid4())

           job_data = {
               'job_id': job_id,
               'spider_name': spider_name,
               'urls': urls,
               'config': config or {},
               'status': 'pending',
               'created_at': datetime.now().isoformat(),
               'worker_id': None,
           }

           # Store job metadata
           self.redis.hset(f'job:{job_id}', mapping=job_data)

           # Queue URLs for processing
           for url in urls:
               url_data = {
                   'job_id': job_id,
                   'url': url,
                   'attempts': 0,
               }
               self.redis.lpush(self.jobs_queue, json.dumps(url_data))

           return job_id

       def get_next_job(self, worker_id):
           """Get next job for worker"""
           job_data = self.redis.brpop(self.jobs_queue, timeout=30)
           if job_data:
               job = json.loads(job_data[1])
               job['worker_id'] = worker_id
               job['started_at'] = datetime.now().isoformat()

               # Update job status
               self.redis.hset(f"job:{job['job_id']}", 'status', 'processing')
               self.redis.hset(f"job:{job['job_id']}", 'worker_id', worker_id)

               return job
           return None

       def mark_job_completed(self, job_id, stats):
           """Mark job as completed with statistics"""
           self.redis.hset(f'job:{job_id}', mapping={
               'status': 'completed',
               'completed_at': datetime.now().isoformat(),
               'stats': json.dumps(stats),
           })

.. code-block:: python

   # spiders/distributed_spider.py
   import scrapy
   import json
   from distributors.job_manager import DistributedJobManager

   class DistributedSpider(scrapy.Spider):
       name = 'distributed'

       def __init__(self, worker_id=None, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.worker_id = worker_id or f'worker_{os.getpid()}'
           self.job_manager = DistributedJobManager()
           self.current_job = None

       def start_requests(self):
           """Get jobs from distributed queue"""
           while True:
               job = self.job_manager.get_next_job(self.worker_id)
               if not job:
                   break

               self.current_job = job
               self.logger.info(f"Processing job {job['job_id']} URL: {job['url']}")

               yield scrapy.Request(
                   job['url'],
                   self.parse,
                   meta={'job_data': job}
               )

       def parse(self, response):
           job_data = response.meta['job_data']

           # Extract data based on spider logic
           for item in self.extract_items(response):
               # Add job metadata to items
               item['job_id'] = job_data['job_id']
               item['worker_id'] = self.worker_id
               yield item

           # Follow links and add to queue if needed
           for link in response.css('a::attr(href)').getall():
               if self.should_follow_link(link):
                   new_job_data = {
                       'job_id': job_data['job_id'],
                       'url': response.urljoin(link),
                       'attempts': 0,
                   }
                   self.job_manager.redis.lpush(
                       self.job_manager.jobs_queue,
                       json.dumps(new_job_data)
                   )

Master-Worker Coordination
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # coordinator/master.py
   import time
   import subprocess
   from multiprocessing import Process
   from distributors.job_manager import DistributedJobManager

   class CrawlMaster:
       def __init__(self, num_workers=4):
           self.num_workers = num_workers
           self.job_manager = DistributedJobManager()
           self.workers = []

       def start_crawl(self, spider_name, urls, config=None):
           """Start distributed crawl with multiple workers"""
           # Create the main job
           job_id = self.job_manager.create_crawl_job(spider_name, urls, config)

           # Start worker processes
           for i in range(self.num_workers):
               worker_id = f'worker_{i}'
               worker_process = Process(
                   target=self.start_worker,
                   args=(spider_name, worker_id, job_id)
               )
               worker_process.start()
               self.workers.append(worker_process)

           return job_id

       def start_worker(self, spider_name, worker_id, job_id):
           """Start individual worker process"""
           cmd = [
               'scrapy', 'crawl', spider_name,
               '-a', f'worker_id={worker_id}',
               '-s', f'JOB_ID={job_id}',
           ]
           subprocess.run(cmd)

       def monitor_crawl(self, job_id):
           """Monitor crawl progress"""
           while True:
               job_status = self.job_manager.redis.hget(f'job:{job_id}', 'status')
               if job_status == b'completed':
                   break

               # Get current statistics
               queue_size = self.job_manager.redis.llen(self.job_manager.jobs_queue)
               print(f"Job {job_id}: Queue size: {queue_size}")

               time.sleep(10)

Database Optimization Strategies
-------------------------------

Connection Pooling and Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``scrapy-ingest`` already batches writes (``INGEST_BATCH_SIZE`` / ``INGEST_FLUSH_INTERVAL``)
through a single ``psycopg2`` or ``PyMySQL`` connection. Extra pooling layers are not required.

Advanced Pipeline Patterns
--------------------------

Multi-Stage Processing Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # pipelines/advanced_pipeline.py
   import asyncio
   import aioredis
   from concurrent.futures import ThreadPoolExecutor
   from scrapy.utils.defer import deferred_from_coro

   class AsyncProcessingPipeline:
       def __init__(self, settings):
           self.redis_url = settings.get('REDIS_URL', 'redis://localhost:6379')
           self.thread_pool = ThreadPoolExecutor(max_workers=10)
           self.processing_queue = 'scrapy:processing'

       def open_spider(self, spider):
           """Initialize async components"""
           self.redis = None
           # Initialize Redis connection
           deferred_from_coro(self._init_redis())

       async def _init_redis(self):
           self.redis = await aioredis.from_url(self.redis_url)

       def process_item(self, item, spider):
           """Process item with multiple stages"""
           # Stage 1: Immediate validation
           self._validate_item(item)

           # Stage 2: Async enrichment
           return deferred_from_coro(self._async_process_item(item, spider))

       async def _async_process_item(self, item, spider):
           """Async processing stages"""
           # Stage 2: Data enrichment
           enriched_item = await self._enrich_item(item)

           # Stage 3: External API calls
           api_data = await self._fetch_external_data(enriched_item)
           enriched_item.update(api_data)

           # Stage 4: Cache results
           await self._cache_item(enriched_item)

           # Stage 5: Queue for further processing
           await self._queue_for_postprocessing(enriched_item)

           return enriched_item

       async def _enrich_item(self, item):
           """Add computed fields and metadata"""
           # Add processing timestamp
           item['processed_at'] = datetime.now().isoformat()

           # Add computed fields
           if 'price' in item and 'original_price' in item:
               item['discount_percentage'] = (
                   (item['original_price'] - item['price']) / item['original_price'] * 100
               )

           return item

       async def _fetch_external_data(self, item):
           """Fetch additional data from external APIs"""
           # Example: Fetch additional product data
           if 'product_id' in item:
               # Simulate API call
               await asyncio.sleep(0.1)
               return {
                   'external_rating': 4.5,
                   'external_reviews': 123,
               }
           return {}

       async def _cache_item(self, item):
           """Cache processed item in Redis"""
           if self.redis:
               cache_key = f"item:{item.get('id', 'unknown')}"
               await self.redis.setex(
                   cache_key,
                   3600,  # 1 hour TTL
                   json.dumps(dict(item))
               )

       async def _queue_for_postprocessing(self, item):
           """Queue item for additional processing"""
           if self.redis:
               await self.redis.lpush(
                   self.processing_queue,
                   json.dumps(dict(item))
               )

Real-time Analytics Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # pipelines/analytics_pipeline.py
   import time
   from collections import defaultdict, deque
   from threading import Lock

   class RealTimeAnalyticsPipeline:
       def __init__(self, settings):
           self.window_size = settings.getint('ANALYTICS_WINDOW_SIZE', 60)  # 60 seconds
           self.metrics = defaultdict(deque)
           self.metrics_lock = Lock()
           self.last_report = time.time()
           self.report_interval = settings.getint('ANALYTICS_REPORT_INTERVAL', 30)

       def process_item(self, item, spider):
           """Collect real-time metrics"""
           current_time = time.time()

           with self.metrics_lock:
               # Update metrics
               self.metrics['items_per_second'].append(current_time)
               self.metrics['categories'][item.get('category', 'unknown')] += 1

               if 'price' in item:
                   self.metrics['price_distribution'].append(float(item['price']))

               # Clean old metrics (sliding window)
               self._clean_old_metrics(current_time)

               # Generate reports periodically
               if current_time - self.last_report > self.report_interval:
                   self._generate_analytics_report(spider)
                   self.last_report = current_time

           return item

       def _clean_old_metrics(self, current_time):
           """Remove metrics outside the time window"""
           cutoff_time = current_time - self.window_size

           # Clean time-based metrics
           while (self.metrics['items_per_second'] and
                  self.metrics['items_per_second'][0] < cutoff_time):
               self.metrics['items_per_second'].popleft()

           # Clean price distribution (keep only recent prices)
           if len(self.metrics['price_distribution']) > 1000:
               self.metrics['price_distribution'] = deque(
                   list(self.metrics['price_distribution'])[-500:],
                   maxlen=1000
               )

       def _generate_analytics_report(self, spider):
           """Generate and log analytics report"""
           items_per_second = len(self.metrics['items_per_second']) / self.window_size

           price_stats = {}
           if self.metrics['price_distribution']:
               prices = list(self.metrics['price_distribution'])
               price_stats = {
                   'avg_price': sum(prices) / len(prices),
                   'min_price': min(prices),
                   'max_price': max(prices),
               }

           report = {
               'timestamp': time.time(),
               'items_per_second': round(items_per_second, 2),
               'category_distribution': dict(self.metrics['categories']),
               'price_statistics': price_stats,
           }

           spider.logger.info(f"Analytics Report: {report}")

           # Send to external monitoring system
           self._send_to_monitoring(report)

       def _send_to_monitoring(self, report):
           """Send metrics to external monitoring system"""
           # Integration with Prometheus, DataDog, etc.
           pass

Integration with External Systems
---------------------------------

Webhook Integration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # integrations/webhook_notifier.py
   import requests
   import json
   from datetime import datetime

   class WebhookNotificationPipeline:
       def __init__(self, settings):
           self.webhook_urls = settings.getlist('WEBHOOK_URLS', [])
           self.notification_types = settings.getlist('WEBHOOK_TYPES', ['item_scraped', 'spider_closed'])
           self.batch_size = settings.getint('WEBHOOK_BATCH_SIZE', 10)
           self.pending_notifications = []

       def process_item(self, item, spider):
           """Queue item notifications"""
           if 'item_scraped' in self.notification_types:
               notification = {
                   'type': 'item_scraped',
                   'spider': spider.name,
                   'job_id': getattr(spider, 'job_id', 'unknown'),
                   'item_count': getattr(spider, 'item_count', 0) + 1,
                   'timestamp': datetime.now().isoformat(),
                   'sample_item': dict(item)  # Include sample data
               }

               self.pending_notifications.append(notification)

               # Send batch when threshold reached
               if len(self.pending_notifications) >= self.batch_size:
                   self._send_batch_notifications()

           return item

       def spider_closed(self, spider):
           """Send final notifications"""
           if 'spider_closed' in self.notification_types:
               stats = spider.crawler.stats.get_stats()
               notification = {
                   'type': 'spider_closed',
                   'spider': spider.name,
                   'job_id': getattr(spider, 'job_id', 'unknown'),
                   'final_stats': {
                       'items_scraped': stats.get('item_scraped_count', 0),
                       'requests_count': stats.get('downloader/request_count', 0),
                       'duration': stats.get('elapsed_time_seconds', 0),
                   },
                   'timestamp': datetime.now().isoformat(),
               }

               self.pending_notifications.append(notification)

           # Send any remaining notifications
           self._send_batch_notifications()

       def _send_batch_notifications(self):
           """Send batch of notifications to all webhooks"""
           if not self.pending_notifications:
               return

           payload = {
               'batch_id': str(uuid.uuid4()),
               'timestamp': datetime.now().isoformat(),
               'notifications': self.pending_notifications.copy()
           }

           for webhook_url in self.webhook_urls:
               try:
                   response = requests.post(
                       webhook_url,
                       json=payload,
                       timeout=5,
                       headers={'Content-Type': 'application/json'}
                   )
                   response.raise_for_status()
               except Exception as e:
                   logger.warning(f"Webhook notification failed for {webhook_url}: {e}")

           self.pending_notifications.clear()

Next Steps
----------

* :doc:`production-deployment` - Complete production deployment guide
* :doc:`troubleshooting` - Common issues and solutions
* :doc:`../api/pipelines` - Detailed API reference
