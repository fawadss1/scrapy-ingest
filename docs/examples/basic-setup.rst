
   # Respectful crawling for news sites
   DOWNLOAD_DELAY = 2
   RANDOMIZE_DOWNLOAD_DELAY = 0.5
   CONCURRENT_REQUESTS_PER_DOMAIN = 2

   # Custom validation pipeline
   class ArticleValidationPipeline:
       def process_item(self, item, spider):
           # Ensure minimum content length
           if len(item.get('content', '')) < 100:
               raise DropItem(f"Article too short: {item.get('title')}")

           # Ensure required fields
           required_fields = ['title', 'content', 'article_url']
           for field in required_fields:
               if not item.get(field):
                   raise DropItem(f"Missing required field: {field}")

           return item

Running with Parameters
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Scrape different categories
   scrapy crawl articles -a category=technology
   scrapy crawl articles -a category=business
   scrapy crawl articles -a category=sports

   # With custom job ID
   scrapy crawl articles -a category=technology -s JOB_ID=tech_news_morning

Monitoring Example
-----------------

Real-time monitoring setup for production use.

Monitoring Spider
~~~~~~~~~~~~~~~

.. code-block:: python

   # monitoring/spiders/health_check.py
   import scrapy
   import psycopg2
   from datetime import datetime, timedelta

   class HealthCheckSpider(scrapy.Spider):
       name = 'health_check'

       def start_requests(self):
           # This spider doesn't make HTTP requests
           # It just checks database health
           yield scrapy.Request('data:,', self.check_database_health)

       def check_database_health(self, response):
           """Check database connectivity and recent activity"""
           try:
               conn = psycopg2.connect(self.settings.get('DB_URL'))
               cursor = conn.cursor()

               # Check recent activity (last 24 hours)
               cursor.execute("""
                   SELECT
                       job_id,
                       COUNT(*) as item_count,
                       MAX(created_at) as last_activity
                   FROM job_items
                   WHERE created_at > NOW() - INTERVAL '24 hours'
                   GROUP BY job_id
               """)

               recent_jobs = cursor.fetchall()

               # Check for errors in logs
               cursor.execute("""
                   SELECT COUNT(*)
                   FROM job_logs
                   WHERE type = 'ERROR'
                   AND created_at > NOW() - INTERVAL '1 hour'
               """)

               recent_errors = cursor.fetchone()[0]

               health_report = {
                   'timestamp': datetime.now().isoformat(),
                   'database_connected': True,
                   'recent_jobs': len(recent_jobs),
                   'total_items_24h': sum(job[1] for job in recent_jobs),
                   'recent_errors_1h': recent_errors,
                   'status': 'healthy' if recent_errors < 10 else 'warning'
               }

               self.logger.info(f"Health check completed: {health_report}")
               yield health_report

           except Exception as e:
               self.logger.error(f"Health check failed: {e}")
               yield {
                   'timestamp': datetime.now().isoformat(),
                   'database_connected': False,
                   'error': str(e),
                   'status': 'critical'
               }

Data Analysis Queries
~~~~~~~~~~~~~~~~~~~

Common queries for analyzing scraped data:

.. code-block:: sql
Basic Setup Examples
   -- Daily scraping summary
   SELECT
       DATE(created_at) as date,
       job_id,
       COUNT(*) as items_scraped
   FROM job_items
   WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
   GROUP BY date, job_id
   ORDER BY date DESC, items_scraped DESC;

   -- Performance analysis
   SELECT
       SPLIT_PART(url, '/', 3) as domain,
       AVG(response_time) as avg_response_time,
       COUNT(*) as request_count,
       COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
   FROM job_requests
   WHERE created_at > CURRENT_DATE - INTERVAL '1 day'
   GROUP BY domain
   ORDER BY request_count DESC;

   -- Content analysis for news articles
   SELECT
       item->>'category' as category,
       COUNT(*) as article_count,
       AVG((item->>'word_count')::int) as avg_word_count,
       AVG((item->>'reading_time_minutes')::int) as avg_reading_time
   FROM job_items
   WHERE item->>'category' IS NOT NULL
   GROUP BY category
   ORDER BY article_count DESC;

Next Steps
----------

* :doc:`advanced-configurations` - More complex setup examples
* :doc:`production-deployment` - Production-ready configurations
* :doc:`troubleshooting` - Common issues and solutions
===================

This section provides complete, working examples for common Scrapy Ingest setups. Each example includes the complete spider code, settings configuration, and expected database output.

Simple E-commerce Scraper
-------------------------

A basic spider that scrapes product information and stores it in PostgreSQL.

Project Structure
~~~~~~~~~~~~~~~~

.. code-block:: text

   ecommerce_scraper/
   ├── scrapy.cfg
   ├── ecommerce_scraper/
   │   ├── __init__.py
   │   ├── items.py
   │   ├── pipelines.py
   │   ├── settings.py
   │   └── spiders/
   │       ├── __init__.py
   │       └── products.py
   └── requirements.txt

Items Definition
~~~~~~~~~~~~~~~

.. code-block:: python

   # ecommerce_scraper/items.py
   import scrapy
   from scrapy import Item, Field

   class ProductItem(Item):
       name = Field()
       price = Field()
       description = Field()
       category = Field()
       brand = Field()
       availability = Field()
       rating = Field()
       review_count = Field()
       image_urls = Field()
       product_url = Field()

Spider Implementation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ecommerce_scraper/spiders/products.py
   import scrapy
   from ecommerce_scraper.items import ProductItem

   class ProductsSpider(scrapy.Spider):
       name = 'products'
       allowed_domains = ['example-store.com']
       start_urls = ['https://example-store.com/products']

       def parse(self, response):
           """Parse category pages and extract product links"""
           # Extract product URLs
           product_links = response.css('.product-item a::attr(href)').getall()

           for link in product_links:
               yield response.follow(link, self.parse_product)

           # Follow pagination
           next_page = response.css('.pagination .next::attr(href)').get()
           if next_page:
               yield response.follow(next_page, self.parse)

       def parse_product(self, response):
           """Extract product details"""
           item = ProductItem()

           item['name'] = response.css('h1.product-title::text').get()
           item['price'] = self.extract_price(response.css('.price::text').get())
           item['description'] = response.css('.product-description::text').get()
           item['category'] = response.css('.breadcrumb li:last-child::text').get()
           item['brand'] = response.css('.product-brand::text').get()
           item['availability'] = response.css('.availability::text').get()
           item['rating'] = self.extract_rating(response.css('.rating::attr(data-rating)').get())
           item['review_count'] = self.extract_number(response.css('.review-count::text').get())
           item['image_urls'] = response.css('.product-images img::attr(src)').getall()
           item['product_url'] = response.url

           yield item

       def extract_price(self, price_text):
           """Clean and extract numeric price"""
           if not price_text:
               return None
           import re
           match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
           return float(match.group()) if match else None

       def extract_rating(self, rating_text):
           """Extract numeric rating"""
           if not rating_text:
               return None
           try:
               return float(rating_text)
           except ValueError:
               return None

       def extract_number(self, text):
           """Extract number from text"""
           if not text:
               return None
           import re
           match = re.search(r'\d+', text)
           return int(match.group()) if match else None

Settings Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ecommerce_scraper/settings.py
   import os
   from dotenv import load_dotenv

   load_dotenv()

   # Scrapy settings
   BOT_NAME = 'ecommerce_scraper'
   SPIDER_MODULES = ['ecommerce_scraper.spiders']
   NEWSPIDER_MODULE = 'ecommerce_scraper.spiders'

   # Database configuration
   DB_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/ecommerce')
   CREATE_TABLES = True
   JOB_ID = f'products_{int(time.time())}'

   # Pipeline configuration
   ITEM_PIPELINES = {
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   # Extension configuration
   EXTENSIONS = {
       'scrapy_ingest.extensions.LoggingExtension': 500,
   }

   # Scrapy performance settings
   ROBOTSTXT_OBEY = True
   CONCURRENT_REQUESTS = 16
   DOWNLOAD_DELAY = 1
   RANDOMIZE_DOWNLOAD_DELAY = 0.5

   # User agent
   USER_AGENT = 'ecommerce_scraper (+http://www.yourdomain.com)'

   # Enable AutoThrottle for respectful crawling
   AUTOTHROTTLE_ENABLED = True
   AUTOTHROTTLE_START_DELAY = 1
   AUTOTHROTTLE_MAX_DELAY = 10
   AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

Requirements File
~~~~~~~~~~~~~~~

.. code-block:: text

   # requirements.txt
   scrapy>=2.5.0
   scrapy-ingest
   python-dotenv
   psycopg2-binary

Environment Setup
~~~~~~~~~~~~~~~

.. code-block:: bash

   # .env file
   DATABASE_URL=postgresql://scrapy_user:secure_password@localhost:5432/ecommerce_db

Running the Spider
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install dependencies
   pip install -r requirements.txt

   # Run the spider
   scrapy crawl products

   # Run with custom settings
   scrapy crawl products -s JOB_ID=products_batch_001

Expected Database Output
~~~~~~~~~~~~~~~~~~~~~~

After running the spider, your database will contain:

**job_items table:**

.. code-block:: json

   {
       "id": 1,
       "item": {
           "name": "Wireless Bluetooth Headphones",
           "price": 79.99,
           "description": "High-quality wireless headphones with noise cancellation",
           "category": "Electronics",
           "brand": "TechBrand",
           "availability": "In Stock",
           "rating": 4.5,
           "review_count": 234,
           "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
           "product_url": "https://example-store.com/wireless-headphones"
       },
       "created_at": "2025-07-21T10:30:00.123456Z",
       "job_id": 1
   }

**job_requests table:**

.. code-block:: text

   | id | url                                      | method | status_code | response_time |
   |----|------------------------------------------|--------|-------------|---------------|
   | 1  | https://example-store.com/products      | GET    | 200         | 0.245         |
   | 2  | https://example-store.com/headphones    | GET    | 200         | 0.189         |

**job_logs table:**

.. code-block:: text

   | id | type | message                           | created_at              |
   |----|------|-----------------------------------|-------------------------|
   | 1  | INFO | Spider opened: products           | 2025-07-21 10:30:00    |
   | 2  | INFO | Successfully processed item       | 2025-07-21 10:30:15    |

News Article Scraper
-------------------

A more complex example that scrapes news articles with full-text content.

Spider Implementation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # news_scraper/spiders/articles.py
   import scrapy
   from datetime import datetime
   import re

   class ArticlesSpider(scrapy.Spider):
       name = 'articles'
       allowed_domains = ['news-site.com']

       def __init__(self, category='technology', *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.category = category
           self.start_urls = [f'https://news-site.com/{category}']

       def parse(self, response):
           """Parse article listing pages"""
           articles = response.css('.article-preview')

           for article in articles:
               article_url = article.css('a::attr(href)').get()
               if article_url:
                   yield response.follow(
                       article_url,
                       self.parse_article,
                       meta={'category': self.category}
                   )

           # Follow pagination
           next_page = response.css('.pagination .next::attr(href)').get()
           if next_page:
               yield response.follow(next_page, self.parse)

       def parse_article(self, response):
           """Extract full article content"""
           # Extract article metadata
           title = response.css('h1.article-title::text').get()
           author = response.css('.author-name::text').get()
           publish_date = self.extract_date(response.css('.publish-date::text').get())

           # Extract article content
           content_paragraphs = response.css('.article-content p::text').getall()
           full_content = '\n'.join(content_paragraphs)

           # Extract tags
           tags = response.css('.article-tags .tag::text').getall()

           # Calculate reading time (average 200 words per minute)
           word_count = len(full_content.split())
           reading_time = max(1, round(word_count / 200))

           item = {
               'title': title,
               'author': author,
               'publish_date': publish_date,
               'category': response.meta.get('category'),
               'content': full_content,
               'word_count': word_count,
               'reading_time_minutes': reading_time,
               'tags': tags,
               'article_url': response.url,
               'scraped_at': datetime.now().isoformat(),
           }

           self.logger.info(f"Scraped article: {title} ({word_count} words)")
           yield item

       def extract_date(self, date_text):
           """Extract and normalize date"""
           if not date_text:
               return None

           # Handle different date formats
           patterns = [
               r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
               r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
               r'(\w+ \d{1,2}, \d{4})',  # Month DD, YYYY
           ]

           for pattern in patterns:
               match = re.search(pattern, date_text)
               if match:
                   return match.group(1)

           return date_text

Settings for News Scraper
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # news_scraper/settings.py
   BOT_NAME = 'news_scraper'

   # Database configuration
   DB_URL = 'postgresql://user:password@localhost:5432/news_db'
   CREATE_TABLES = True
   JOB_ID = 'news_daily_scrape'

   # Pipelines
   ITEM_PIPELINES = {
       'news_scraper.pipelines.ArticleValidationPipeline': 200,
       'scrapy_ingest.pipelines.DbInsertPipeline': 300,
   }

   EXTENSIONS = {
       'scrapy_ingest.extensions.LoggingExtension': 500,
   }

