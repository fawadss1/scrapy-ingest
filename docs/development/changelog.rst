Changelog
=========

All notable changes to Scrapy Item Ingest will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_, and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[0.2.8] - 2026-09-01
--------------------

### Added
- Shared batch collector for items, requests, logs, and stats (flush on batch size, every 10s, and engine stop)
- Automatic enable of request logging, error logging, parent_url tracking, job logs, and stats from ``DbInsertPipeline`` alone
- Crawl-graph ``parent_url`` via scraper hooks and a fingerprint map (start URLs are ``null``)
- Failed-request capture through injected error middleware (``error`` + ``success`` columns)
- Full job logs: early/startup buffer, Scrapy/Twisted/warnings, exceptions, and ``print()`` capture
- Scrapy crawl stats stored on ``jobs.stats`` (no separate ``job_stats`` table)
- ``INGEST_BATCH_SIZE`` and ``INGEST_FLUSH_INTERVAL`` settings
- Discrete ``DB_*`` fields now build a connection URL (no ``DB_URL`` required)
- Auto-generated unique ``job_id`` when ``JOB_ID`` is not set (``spider-YYYYMMDDHHMMSS-xxxxxxxx``)
- ``jobs`` table with per-crawl status, item/request/error/log counts, crawl speed, finish reason, and stats
- Child tables store ``jobs.id`` (integer) in ``job_id``, with ``ON DELETE CASCADE``

### Changed
- Request fingerprint is SHA1 of method + canonical URL (used for parent_url lookup)
- ``LoggingExtension`` follows Scrapy ``LOG_LEVEL`` and writes structured log rows (index, time, logger, exception)
- Items are buffered and batch-inserted instead of one commit per item
- Recommended enable path is now ``scrapy_item_ingest.pipelines.DbInsertPipeline`` (the short ``scrapy_item_ingest.DbInsertPipeline`` alias still works)
- ``parent_id`` is now set from ``parent_url`` after each request flush

[Unreleased]
------------

### Added
- Advanced batch processing with configurable batch sizes
- Connection pooling optimization for high-throughput scenarios
- Redis-based job queue system for distributed crawling
- Comprehensive monitoring and metrics collection
- Webhook notifications for real-time updates
- Custom serialization handlers for complex data types

### Deprecated
- Legacy table naming conventions (will be removed in v2.0.0)

### Security
- Enhanced database connection security with SSL support
- Input validation improvements to prevent SQL injection


[0.2.7] - 2025-11-24
--------------------

### Fixed
- Update getting error logs and insertions logic [scrapy_item_ingest.pipelines.items]


[0.2.3] - 2025-11-21
--------------------

### Fixed
- Removed extra loging from [scrapy_item_ingest.pipelines.items]


[0.2.2] - 2025-11-21
--------------------

### Changed
- Simplified the logging extension to only attach to the root logger, which prevents log duplication and captures all log sources.
- Removed complex and unnecessary logging settings (`LOG_DB_LOGGERS`, `LOG_DB_EXCLUDE_LOGGERS`, `LOG_DB_EXCLUDE_PATTERNS`, `LOG_DB_DEDUP_TTL`, `LOG_DB_CAPTURE_LEVEL`). The extension now relies on the standard Scrapy `LOG_LEVEL`.

### Fixed
- Resolved an issue where logs from the `root` logger were not being captured.
- Fixed a log duplication issue caused by attaching the database handler to multiple loggers in the same hierarchy.

[0.2.0] - 2025-11-11
-------------------

### Added
- Automatic DSN normalization for PostgreSQL `DB_URL` to safely handle special characters in credentials (e.g., `@`, `$`)
- Unified `DatabaseConnection` singleton API used across pipelines and extensions (`connect/execute/commit/rollback/close`)
- Logging extension now capable of capturing Scrapy framework logs (Zyte-like) in addition to spider logs
- Console-like formatter in DB logs honoring `LOG_FORMAT` and `LOG_DATEFORMAT`
- Fine-grained logging controls for DB persistence:
  - Allowlist by logger namespaces via `LOG_DB_LOGGERS`
  - Exclude by namespaces via `LOG_DB_EXCLUDE_LOGGERS`
  - Exclude by message substrings via `LOG_DB_EXCLUDE_PATTERNS`
  - Batch size via `LOG_DB_BATCH_SIZE`
  - Duplicate suppression via `LOG_DB_DEDUP_TTL`

### Changed
- Attached the DB log handler only to the spider’s base logger and the top-level `scrapy` logger to avoid propagation duplicates
- Applied optional `LOG_DB_CAPTURE_LEVEL` (default falls back to `LOG_DB_LEVEL`) to increase capture detail for DB without changing console verbosity
- Normalized schema for logs to consistently use `level` (instead of `type`)
- Simplified and streamlined documentation and README; reduced pages to essentials

### Fixed
- Import errors in external integrations expecting `DatabaseConnection` by providing a compatibility alias to `DBConnection`
- Eliminated repeated DB logging errors by throttling after the first failure
- Reduced noise by default: excluded `scrapy.core.scraper` and messages containing `Scraped from <` from DB persistence

### Settings (new/updated)
- `LOG_DB_LEVEL`: minimum level stored in DB (default: `DEBUG`)
- `LOG_DB_CAPTURE_LEVEL`: capture level for attached loggers (DB only)
- `LOG_DB_LOGGERS`: additional allowed logger prefixes (defaults always include `[spider.name, 'scrapy']`)
- `LOG_DB_EXCLUDE_LOGGERS`: logger namespaces to exclude (default: `['scrapy.core.scraper']`)
- `LOG_DB_EXCLUDE_PATTERNS`: message substrings to exclude (default: `['Scraped from <']`)
- `LOG_DB_BATCH_SIZE`: DB insert batch size
- `LOG_DB_DEDUP_TTL`: seconds to suppress duplicates

[0.1.1] - 2025-07-21
-------------------

### Added
- **Core Pipeline Functionality**
  - `DbInsertPipeline` - Combined pipeline for items and requests
  - `ItemsPipeline` - Standalone items processing pipeline
  - `RequestsPipeline` - Standalone requests tracking pipeline
  - `BasePipeline` - Base class for custom implementations

- **Database Integration**
  - PostgreSQL database support with automatic table creation
  - JSONB storage for flexible item data structure
  - Request tracking with parent-child relationships
  - Performance optimized with proper indexing

- **Logging Extension**
  - `LoggingExtension` - Comprehensive spider event logging
  - Real-time log storage in database
  - Support for all Python log levels
  - Spider lifecycle event tracking

- **Configuration Management**
  - Flexible settings validation
  - Environment-based configuration
  - Multi-environment support (dev, staging, production)
  - Automatic fallback to spider name for job IDs

- **Database Schema**
  - `job_items` table for scraped data storage
  - `job_requests` table for request/response tracking
  - `job_logs` table for spider events and messages
  - Foreign key relationships and proper constraints

- **Utility Functions**
  - Item serialization with datetime and Decimal support
  - Request fingerprinting for deduplication
  - Database connection management
  - Data validation and cleaning utilities

- **Production Features**
  - Docker container support
  - Kubernetes deployment configurations
  - Monitoring and alerting integration
  - High-availability database setup

- **Developer Tools**
  - Comprehensive test suite with pytest
  - Development environment setup
  - Code quality tools (Black, flake8, mypy)
  - Pre-commit hooks configuration

### Documentation
- Complete ReadTheDocs documentation
- Installation and quick start guides
- API reference for all components
- Production deployment examples
- Troubleshooting guide
- Contributing guidelines

### Technical Details

**Database Schema:**

.. code-block:: sql

   -- Items table
   CREATE TABLE job_items (
       id BIGSERIAL PRIMARY KEY,
       item JSONB NOT NULL,
       created_at TIMESTAMPTZ NOT NULL,
       job_id INTEGER NOT NULL
   );

   -- Requests table
   CREATE TABLE job_requests (
       id BIGSERIAL PRIMARY KEY,
       url VARCHAR(200) NOT NULL,
       method VARCHAR(10) NOT NULL,
       status_code INTEGER,
       response_time FLOAT,
       fingerprint VARCHAR(255),
       parent_url VARCHAR(255),
       created_at TIMESTAMPTZ NOT NULL,
       job_id INTEGER NOT NULL,
       parent_id BIGINT,
       FOREIGN KEY (parent_id) REFERENCES job_requests(id)
   );

   -- Logs table
   CREATE TABLE job_logs (
       id BIGSERIAL PRIMARY KEY,
       job_id INTEGER NOT NULL,
       type VARCHAR(50) NOT NULL,
       message TEXT NOT NULL,
       created_at TIMESTAMPTZ NOT NULL
   );

**Configuration Options:**

- `DB_URL` - PostgreSQL connection string (required)
- `CREATE_TABLES` - Auto-create tables (default: True)
- `JOB_ID` - Job identifier (default: spider name)
- `DB_SETTINGS` - Advanced database configuration
- `TABLE_NAMES` - Custom table name mapping

**Pipeline Integration:**

.. code-block:: python

   # Basic setup
   ITEM_PIPELINES = {
       'scrapy_item_ingest.DbInsertPipeline': 300,
   }

   EXTENSIONS = {
       'scrapy_item_ingest.LoggingExtension': 500,
   }

**Key Features:**

- **Real-time Data Storage**: Items and requests stored as they're processed
- **Flexible Data Structure**: JSONB storage supports any item structure
- **Request Tracking**: Complete request/response lifecycle tracking
- **Performance Optimized**: Connection pooling and batch processing
- **Production Ready**: Docker, Kubernetes, and monitoring support
- **Developer Friendly**: Comprehensive documentation and testing

### Breaking Changes
None (initial release)

### Migration Guide
Not applicable (initial release)

---

## Release Notes Template

For future releases, use this template:

```markdown
[X.Y.Z] - YYYY-MM-DD
--------------------

### Added
- New features and capabilities

### Changed
- Changes to existing functionality

### Deprecated
- Features marked for removal in future versions

### Removed
- Features removed in this version

### Fixed
- Bug fixes and corrections

### Security
- Security-related improvements

### Breaking Changes
- Changes that break backward compatibility

### Migration Guide
- Instructions for upgrading from previous versions
```

## Changelog Guidelines

### Categories

**Added** - for new features
**Changed** - for changes in existing functionality
**Deprecated** - for soon-to-be removed features
**Removed** - for now removed features
**Fixed** - for any bug fixes
**Security** - in case of vulnerabilities

### Format

- Use past tense for all entries
- Include issue/PR references where applicable
- Group related changes under subheadings
- Provide migration instructions for breaking changes
- Include code examples for significant new features

### Examples

```markdown
### Added
- New `BatchProcessor` class for high-performance item processing (#123)
- Support for MySQL databases in addition to PostgreSQL (#145)
- Real-time metrics collection via Prometheus integration (#167)

### Changed
- Improved error handling in database connections with automatic retry (#134)
- Updated default batch size from 100 to 500 items for better performance (#156)

### Fixed
- Fixed memory leak in long-running spiders (#142)
- Resolved issue with Unicode characters in item serialization (#158)

### Breaking Changes
- Renamed `table_prefix` setting to `table_names` for consistency
- Changed default job ID format from timestamp to spider name

  **Migration:** Update your settings.py:
  ```python
  # Old
  TABLE_PREFIX = 'custom_'

  # New
  TABLE_NAMES = {
      'items': 'custom_items',
      'requests': 'custom_requests',
      'logs': 'custom_logs'
  }
  ```
```
