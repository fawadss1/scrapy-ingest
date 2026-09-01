Production Deployment
===================

This guide covers deploying Scrapy Ingest in production environments with proper scaling, monitoring, and reliability patterns.

Production Architecture Overview
-------------------------------

Recommended Production Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │   Load Balancer │    │   Scrapy Nodes  │    │   PostgreSQL    │
   │    (Nginx)      │───▶│    (Multiple)   │───▶│    Cluster      │
   └─────────────────┘    └─────────────────┘    └─────────────────┘
            │                       │                       │
            │                       │                       │
   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │   Monitoring    │    │   Redis Queue   │    │   File Storage  │
   │ (Prometheus)    │    │   (Job Queue)   │    │      (S3)       │
   └─────────────────┘    └─────────────────┘    └─────────────────┘

Docker Production Setup
----------------------

Multi-Container Docker Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.prod.yml
   version: '3.8'

   services:
     scrapy-master:
       build:
         context: .
         dockerfile: Dockerfile.scrapy
       environment:
         - SCRAPY_ENV=production
         - DATABASE_URL=postgresql://scrapy:${DB_PASSWORD}@postgres:5432/scrapy_prod
         - REDIS_URL=redis://redis:6379/0
         - JOB_ID=prod_${SPIDER_NAME}_${TIMESTAMP}
       depends_on:
         - postgres
         - redis
       volumes:
         - ./logs:/app/logs
         - ./data:/app/data
       networks:
         - scrapy-network
       deploy:
         replicas: 1
         resources:
           limits:
             cpus: '2.0'
             memory: 4G

     scrapy-workers:
       build:
         context: .
         dockerfile: Dockerfile.scrapy
       environment:
         - SCRAPY_ENV=production
         - DATABASE_URL=postgresql://scrapy:${DB_PASSWORD}@postgres:5432/scrapy_prod
         - REDIS_URL=redis://redis:6379/0
         - WORKER_MODE=true
       depends_on:
         - postgres
         - redis
         - scrapy-master
       volumes:
         - ./logs:/app/logs
       networks:
         - scrapy-network
       deploy:
         replicas: 4
         resources:
           limits:
             cpus: '1.0'
             memory: 2G

     postgres:
       image: postgres:15-alpine
       environment:
         POSTGRES_DB: scrapy_prod
         POSTGRES_USER: scrapy
         POSTGRES_PASSWORD: ${DB_PASSWORD}
         POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --locale=C"
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
       ports:
         - "5432:5432"
       networks:
         - scrapy-network
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 8G

     redis:
       image: redis:7-alpine
       command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
       volumes:
         - redis_data:/data
       ports:
         - "6379:6379"
       networks:
         - scrapy-network
       deploy:
         resources:
           limits:
             cpus: '0.5'
             memory: 1G

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf
         - ./nginx/ssl:/etc/nginx/ssl
       depends_on:
         - scrapy-master
       networks:
         - scrapy-network

     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
         - prometheus_data:/prometheus
       networks:
         - scrapy-network

     grafana:
       image: grafana/grafana:latest
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
       volumes:
         - grafana_data:/var/lib/grafana
         - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
       networks:
         - scrapy-network

   volumes:
     postgres_data:
     redis_data:
     prometheus_data:
     grafana_data:

   networks:
     scrapy-network:
       driver: bridge

Production Dockerfile
~~~~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   # Dockerfile.scrapy
   FROM python:3.11-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       libpq-dev \
       curl \
       && rm -rf /var/lib/apt/lists/*

   # Create app user
   RUN useradd --create-home --shell /bin/bash scrapy
   WORKDIR /app
   COPY requirements.txt .

   # Install Python dependencies
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .
   RUN chown -R scrapy:scrapy /app

   # Switch to non-root user
   USER scrapy

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
     CMD python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" || exit 1

   # Default command
   CMD ["python", "-m", "scrapy", "crawl", "$SPIDER_NAME"]

Kubernetes Deployment
---------------------

Production Kubernetes Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # k8s/namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: scrapy-production

   ---
   # k8s/configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: scrapy-config
     namespace: scrapy-production
   data:
     SCRAPY_ENV: "production"
     LOG_LEVEL: "INFO"
     CONCURRENT_REQUESTS: "32"
     DOWNLOAD_DELAY: "0.1"

   ---
   # k8s/secret.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: scrapy-secrets
     namespace: scrapy-production
   type: Opaque
   data:
     DATABASE_URL: <base64-encoded-database-url>
     REDIS_URL: <base64-encoded-redis-url>

   ---
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: scrapy-workers
     namespace: scrapy-production
   spec:
     replicas: 6
     selector:
       matchLabels:
         app: scrapy-workers
     template:
       metadata:
         labels:
           app: scrapy-workers
       spec:
         containers:
         - name: scrapy
           image: your-registry/scrapy-ingest:latest
           envFrom:
           - configMapRef:
               name: scrapy-config
           - secretRef:
               name: scrapy-secrets
           resources:
             requests:
               memory: "1Gi"
               cpu: "500m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
           livenessProbe:
             exec:
               command:
               - python
               - -c
               - "import psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])"
             initialDelaySeconds: 30
             periodSeconds: 60
           readinessProbe:
             exec:
               command:
               - python
               - -c
               - "import redis; redis.from_url(os.environ['REDIS_URL']).ping()"
             initialDelaySeconds: 10
             periodSeconds: 30

   ---
   # k8s/cronjob.yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: daily-scrape
     namespace: scrapy-production
   spec:
     schedule: "0 2 * * *"  # Daily at 2 AM
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: scrapy
               image: your-registry/scrapy-ingest:latest
               command:
               - python
               - -m
               - scrapy
               - crawl
               - products
               - -s
               - JOB_ID=daily_$(date +%Y%m%d_%H%M%S)
               envFrom:
               - configMapRef:
                   name: scrapy-config
               - secretRef:
                   name: scrapy-secrets
             restartPolicy: OnFailure

Database Production Setup
------------------------

PostgreSQL High Availability
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sql

   -- Production database initialization
   -- Create dedicated database and user
   CREATE DATABASE scrapy_production
   WITH ENCODING 'UTF8'
   LC_COLLATE='en_US.UTF-8'
   LC_CTYPE='en_US.UTF-8';

   CREATE USER scrapy_prod WITH PASSWORD 'secure_production_password';
   GRANT ALL PRIVILEGES ON DATABASE scrapy_production TO scrapy_prod;

   -- Connect to production database
   \c scrapy_production;

   -- Create optimized tables with partitioning
   CREATE TABLE job_items (
       id BIGSERIAL,
       item JSONB NOT NULL,
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       job_id INTEGER NOT NULL
   ) PARTITION BY RANGE (created_at);

   -- Create monthly partitions
   CREATE TABLE job_items_2025_01 PARTITION OF job_items
   FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

   CREATE TABLE job_items_2025_02 PARTITION OF job_items
   FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

   -- Create indexes for performance
   CREATE INDEX CONCURRENTLY idx_job_items_job_id ON job_items(job_id);
   CREATE INDEX CONCURRENTLY idx_job_items_created_at ON job_items(created_at);
   CREATE INDEX CONCURRENTLY idx_job_items_item_gin ON job_items USING GIN(item);

   -- Similar partitioning for other tables
   CREATE TABLE job_requests (
       id BIGSERIAL,
       url VARCHAR(500) NOT NULL,
       method VARCHAR(10) NOT NULL,
       status_code INTEGER,
       response_time FLOAT,
       fingerprint VARCHAR(255),
       parent_url VARCHAR(500),
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       job_id INTEGER NOT NULL,
       parent_id BIGINT
   ) PARTITION BY RANGE (created_at);

   -- Performance tuning
   ALTER SYSTEM SET shared_buffers = '2GB';
   ALTER SYSTEM SET effective_cache_size = '6GB';
   ALTER SYSTEM SET maintenance_work_mem = '512MB';
   ALTER SYSTEM SET checkpoint_completion_target = 0.9;
   ALTER SYSTEM SET wal_buffers = '16MB';
   ALTER SYSTEM SET default_statistics_target = 100;
   ALTER SYSTEM SET random_page_cost = 1.1;

Database Backup Strategy
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # backup_script.sh - Automated database backup

   DB_NAME="scrapy_production"
   DB_USER="scrapy_prod"
   BACKUP_DIR="/backups/postgresql"
   S3_BUCKET="your-backup-bucket"
   RETENTION_DAYS=30

   # Create backup with compression
   pg_dump -h localhost -U $DB_USER -d $DB_NAME \
     --format=custom \
     --compress=9 \
     --verbose \
     --file=$BACKUP_DIR/scrapy_backup_$(date +%Y%m%d_%H%M%S).dump

   # Upload to S3
   aws s3 cp $BACKUP_DIR/scrapy_backup_*.dump s3://$S3_BUCKET/daily/

   # Clean old local backups
   find $BACKUP_DIR -name "scrapy_backup_*.dump" -mtime +$RETENTION_DAYS -delete

   # Verify backup integrity
   pg_restore --list $BACKUP_DIR/scrapy_backup_*.dump > /dev/null
   if [ $? -eq 0 ]; then
     echo "Backup completed successfully"
   else
     echo "Backup verification failed" | mail -s "Backup Alert" admin@yourcompany.com
   fi

Monitoring and Alerting
----------------------

Production Monitoring Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # monitoring/metrics_collector.py
   import psycopg2
   import redis
   import time
   from prometheus_client import Gauge, Counter, start_http_server

   class ScrapyMetricsCollector:
       def __init__(self, db_url, redis_url):
           self.db_url = db_url
           self.redis_url = redis_url

           # Prometheus metrics
           self.items_scraped = Gauge('scrapy_items_scraped_total', 'Total items scraped', ['job_id'])
           self.requests_made = Gauge('scrapy_requests_made_total', 'Total requests made', ['job_id'])
           self.error_rate = Gauge('scrapy_error_rate', 'Error rate percentage', ['job_id'])
           self.avg_response_time = Gauge('scrapy_avg_response_time_seconds', 'Average response time', ['job_id'])
           self.active_jobs = Gauge('scrapy_active_jobs', 'Number of active jobs')
           self.queue_size = Gauge('scrapy_queue_size', 'Size of job queue')

       def collect_metrics(self):
           """Collect metrics from database and Redis"""
           # Database metrics
           with psycopg2.connect(self.db_url) as conn:
               cursor = conn.cursor()

               # Active jobs metrics
               cursor.execute("""
                   SELECT
                       job_id,
                       COUNT(DISTINCT ji.id) as items_count,
                       COUNT(DISTINCT jr.id) as requests_count,
                       AVG(jr.response_time) as avg_response_time,
                       COUNT(CASE WHEN jr.status_code >= 400 THEN 1 END) * 100.0 / COUNT(jr.id) as error_rate
                   FROM job_items ji
                   LEFT JOIN job_requests jr ON ji.job_id = jr.job_id
                   WHERE ji.created_at > NOW() - INTERVAL '1 hour'
                   GROUP BY job_id
               """)

               for row in cursor.fetchall():
                   job_id, items, requests, avg_time, error_rate = row
                   self.items_scraped.labels(job_id=job_id).set(items or 0)
                   self.requests_made.labels(job_id=job_id).set(requests or 0)
                   self.avg_response_time.labels(job_id=job_id).set(avg_time or 0)
                   self.error_rate.labels(job_id=job_id).set(error_rate or 0)

               # Count active jobs
               cursor.execute("""
                   SELECT COUNT(DISTINCT job_id)
                   FROM job_items
                   WHERE created_at > NOW() - INTERVAL '1 hour'
               """)
               active_jobs = cursor.fetchone()[0]
               self.active_jobs.set(active_jobs)

           # Redis metrics
           r = redis.from_url(self.redis_url)
           queue_size = r.llen('scrapy:jobs')
           self.queue_size.set(queue_size)

       def start_metrics_server(self, port=8000):
           """Start Prometheus metrics server"""
           start_http_server(port)

           while True:
               try:
                   self.collect_metrics()
                   time.sleep(30)  # Collect every 30 seconds
               except Exception as e:
                   print(f"Metrics collection error: {e}")
                   time.sleep(60)

Alerting Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # monitoring/alerts.yml - Prometheus alerting rules
   groups:
   - name: scrapy_alerts
     rules:
     - alert: ScrapyHighErrorRate
       expr: scrapy_error_rate > 10
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High error rate detected in Scrapy job {{ $labels.job_id }}"
         description: "Error rate is {{ $value }}% for job {{ $labels.job_id }}"

     - alert: ScrapySlowResponseTime
       expr: scrapy_avg_response_time_seconds > 5
       for: 10m
       labels:
         severity: warning
       annotations:
         summary: "Slow response times in Scrapy job {{ $labels.job_id }}"
         description: "Average response time is {{ $value }} seconds"

     - alert: ScrapyQueueBacklog
       expr: scrapy_queue_size > 10000
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "Large queue backlog detected"
         description: "Queue size is {{ $value }} items"

     - alert: ScrapyNoActiveJobs
       expr: scrapy_active_jobs == 0
       for: 30m
       labels:
         severity: warning
       annotations:
         summary: "No active Scrapy jobs detected"
         description: "No jobs have been active for 30 minutes"

Performance Optimization
-----------------------

Production Performance Tuning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings/production_optimized.py
   import os

   # High-performance Scrapy settings
   CONCURRENT_REQUESTS = 64
   CONCURRENT_REQUESTS_PER_DOMAIN = 32
   DOWNLOAD_DELAY = 0.05
   RANDOMIZE_DOWNLOAD_DELAY = 0.1

   # Memory optimization
   MEMUSAGE_ENABLED = True
   MEMUSAGE_LIMIT_MB = 2048
   MEMUSAGE_WARNING_MB = 1536

   # Connection pooling
   REACTOR_THREADPOOL_MAXSIZE = 20

   # Download optimizations
   DOWNLOAD_TIMEOUT = 15
   DOWNLOAD_MAXSIZE = 1073741824  # 1GB
   DOWNLOAD_WARNSIZE = 33554432   # 32MB

   # DNS caching
   DNSCACHE_ENABLED = True
   DNSCACHE_SIZE = 10000

   # Database optimizations
   DB_SETTINGS = {
       'pool_size': 30,
       'max_overflow': 50,
       'pool_timeout': 30,
       'pool_recycle': 3600,
       'pool_pre_ping': True,
   }

   # Batch processing
   BATCH_SIZE = 1000
   BATCH_TIMEOUT = 30

   # Logging optimization
   LOG_LEVEL = 'INFO'
   LOG_STDOUT = False
   LOG_FILE = '/app/logs/scrapy.log'

Security Configuration
--------------------

Production Security Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # security/production_security.py
   import os

   # Database security
   DB_URL = os.getenv('DATABASE_URL')  # Never hardcode credentials
   DB_SSL_MODE = 'require'

   # Redis security
   REDIS_URL = os.getenv('REDIS_URL')
   REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

   # Network security
   DOWNLOAD_HANDLERS = {
       'http': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
       'https': 'scrapy.core.downloader.handlers.http.HTTPSDownloadHandler',
   }

   # User agent rotation
   USER_AGENT_LIST = [
       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
       'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
       'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
   ]

   # Request filtering
   ROBOTSTXT_OBEY = True
   HTTPCACHE_ENABLED = False  # Disable in production
   COOKIES_ENABLED = False    # Disable unless needed

   # Rate limiting
   AUTOTHROTTLE_ENABLED = True
   AUTOTHROTTLE_START_DELAY = 0.1
   AUTOTHROTTLE_MAX_DELAY = 10
   AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0

Deployment Automation
-------------------

CI/CD Pipeline
~~~~~~~~~~~~~

.. code-block:: yaml

   # .github/workflows/deploy.yml
   name: Deploy to Production

   on:
     push:
       branches: [main]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - name: Set up Python
         uses: actions/setup-python@v3
         with:
           python-version: '3.11'
       - name: Install dependencies
         run: |
           pip install -r requirements.txt
           pip install -r requirements-test.txt
       - name: Run tests
         run: pytest tests/
       - name: Run linting
         run: flake8 scrapy_ingest/

     build:
       needs: test
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - name: Build Docker image
         run: |
           docker build -t scrapy-ingest:${{ github.sha }} .
           docker tag scrapy-ingest:${{ github.sha }} scrapy-ingest:latest
       - name: Push to registry
         run: |
           echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
           docker push scrapy-ingest:${{ github.sha }}
           docker push scrapy-ingest:latest

     deploy:
       needs: build
       runs-on: ubuntu-latest
       steps:
       - name: Deploy to production
         run: |
           kubectl set image deployment/scrapy-workers scrapy=scrapy-ingest:${{ github.sha }}
           kubectl rollout status deployment/scrapy-workers

Next Steps
----------

* :doc:`troubleshooting` - Common production issues and solutions
* :doc:`../api/pipelines` - Detailed API reference
* :doc:`../development/contributing` - Contributing guidelines
