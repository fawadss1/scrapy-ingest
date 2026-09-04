# Scrapy Ingest

[![PyPI version](https://img.shields.io/pypi/v/scrapy-ingest?color=blue)](https://pypi.org/project/scrapy-ingest/)
[![Python versions](https://img.shields.io/pypi/pyversions/scrapy-ingest)](https://pypi.org/project/scrapy-ingest/)
[![Downloads](https://static.pepy.tech/badge/scrapy-ingest)](https://pepy.tech/project/scrapy-ingest)
[![Documentation](https://readthedocs.org/projects/scrapy-ingest/badge/?version=latest)](https://scrapy-ingest.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/fawadss1/scrapy-ingest/blob/master/LICENSE)
[![Changelog](https://img.shields.io/badge/changelog-releases-informational)](https://github.com/fawadss1/scrapy-ingest/releases)

A Scrapy addon that saves **items, requests, logs, and stats** to **PostgreSQL**, **MySQL**, **Elasticsearch**, or **OpenSearch** — with parent_url tracking, failed-request errors, and full job log capture (including `print()`).

You choose where data goes by setting connection URLs — relational database, Elasticsearch/OpenSearch, or **both**.

## Install

```bash
pip install scrapy-ingest
```

This installs all runtime dependencies, including `psycopg2-binary`, `PyMySQL`, and `opensearch-py`.

## Minimal setup (settings.py)

Only the item pipeline is required — requests, logs, stats, parent_url, and error logging are enabled automatically:

```python
ITEM_PIPELINES = {
    "scrapy_ingest.pipelines.DbInsertPipeline": 300,
}

DB_URL = "postgresql://user:password@localhost:5432/database"
```

Run your spider:

```bash
scrapy crawl your_spider
```

Log level follows Scrapy `LOG_LEVEL`.

## Choose your destination

Set **`DB_URL`** (or `DB_*` fields) for Postgres/MySQL, **`SEARCH_URL`** for Elasticsearch/OpenSearch, or both. **At least one must be configured.**

| Mode                                | Settings                | Result                                   |
|-------------------------------------|-------------------------|------------------------------------------|
| **Database only**                   | `DB_URL` or `DB_*`      | SQL only                                 |
| **Elasticsearch / OpenSearch only** | `SEARCH_URL`            | Indexes only                             |
| **Both**                            | `DB_URL` + `SEARCH_URL` | SQL first, then Elasticsearch/OpenSearch |

```python
# Database only
DB_URL = "postgresql://user:password@localhost:5432/database"

# Elasticsearch / OpenSearch only
SEARCH_URL = "http://localhost:9200"

# Both
DB_URL = "postgresql://user:password@localhost:5432/database"
SEARCH_URL = "http://localhost:9200"
```

When both are configured, SQL is written first, then Elasticsearch/OpenSearch indexes. An indexing failure after a successful SQL write is logged but does not roll back database rows.

## Database configuration

PostgreSQL or MySQL — pick **one** connection style.

**Single URL:**

```python
DB_URL = "postgresql://user:password@localhost:5432/database"
# DB_URL = "mysql://user:password@localhost:3306/database"
```

**Discrete fields** (no URL encoding for special characters in passwords):

```python
DB_TYPE = "postgres"   # or "mysql" / "mariadb"
DB_HOST = "localhost"
DB_PORT = 5432         # MySQL: 3306
DB_USER = "user"
DB_PASSWORD = "password"
DB_NAME = "database"
```

Tables are created automatically when `CREATE_TABLES = True` (default).

## Elasticsearch / OpenSearch configuration

Elasticsearch and OpenSearch use the same REST bulk API. The package connects via **`opensearch-py`**, which works with both.

**Minimum:**

```python
SEARCH_URL = "http://localhost:9200"
```

**With authentication (optional):**

```python
SEARCH_URL = "https://search.example.com:9200"
SEARCH_USER = "elastic"
SEARCH_PASSWORD = "secret"
SEARCH_SSL_VERIFY = True   # set False only for self-signed certs in dev
```

**Index names** use the prefix `ingest` by default:

| Index                 | Contents                                              |
|-----------------------|-------------------------------------------------------|
| `ingest-jobs`         | Job metadata: status, counts, elapsed time, stats     |
| `ingest-job_items`    | Scraped items as JSON documents                       |
| `ingest-job_requests` | Requests: url, fingerprint, parent_url, status, error |
| `ingest-job_logs`     | Log lines: level, logger, message, exception          |

Override the prefix:

```python
SEARCH_INDEX_PREFIX = "my_crawl"
# → my_crawl-jobs, my_crawl-job_items, ...
```

Table name settings (`JOBS_TABLE`, `ITEMS_TABLE`, etc.) also apply as the suffix part of index names.

Indexes are created on first write if they do not exist.

## What is stored

### Relational database (Postgres / MySQL)

| Table          | Contents                                                                                                |
|----------------|---------------------------------------------------------------------------------------------------------|
| `jobs`         | One row per crawl: `id`, unique `job_id` string, spider, status, start/finish, counts, items/min, stats |
| `job_items`    | JSON items (`crawled_at` added). `job_id` = `jobs.id` (CASCADE)                                         |
| `job_requests` | url, parent_url, parent_id, status, response_time_secs, fingerprint, error, success                     |
| `job_logs`     | time, logger, level, message, exception                                                                 |

Request `parent_url` is the page that scheduled the request (e.g. sitemap → product). Start URLs are `null`. The request `fingerprint` is a SHA1 hash of method + canonical URL for parent lookup.

### Elasticsearch / OpenSearch

Same crawl data as JSON documents in the indexes listed above. Documents include the string `job_id` (not the integer SQL primary key). Elasticsearch/OpenSearch mode does not link `parent_id`; `parent_url` is stored on each request document.

## Batch flush and crawl summary

Data flushes on batch size, every 10 seconds, and on engine/process stop.

When the spider closes, a crawl summary is printed to stderr (visible even when `LOG_LEVEL` is `ERROR`) with job id, spider, database URL, Elasticsearch/OpenSearch URL, table/index names, counts, and elapsed time. Set `INGEST_SHOW_SUMMARY = False` to hide it.

## Useful settings

| Setting                                                     | Default        | Description                                                 |
|-------------------------------------------------------------|----------------|-------------------------------------------------------------|
| `DB_URL` / `DB_*`                                           | —              | Database connection (enables SQL ingest)                    |
| `SEARCH_URL`                                                | —              | Elasticsearch or OpenSearch URL (enables indexing)          |
| `SEARCH_USER` / `SEARCH_PASSWORD`                           | —              | HTTP basic auth for Elasticsearch/OpenSearch (optional)     |
| `SEARCH_INDEX_PREFIX`                                       | `ingest`       | Prefix for index names                                      |
| `SEARCH_SSL_VERIFY`                                         | `True`         | Verify HTTPS certificates                                   |
| `CREATE_TABLES`                                             | `True`         | Auto-create SQL tables on startup                           |
| `INGEST_BATCH_SIZE`                                         | `50`           | Flush when this many rows are buffered                      |
| `INGEST_FLUSH_INTERVAL`                                     | `10`           | Periodic flush in seconds                                   |
| `INGEST_SHOW_SUMMARY`                                       | `True`         | Print crawl summary when the spider closes                  |
| `DB_TYPE`                                                   | `postgres`     | `postgres` / `mysql` / `mariadb` for discrete `DB_*` fields |
| `ITEMS_TABLE`, `REQUESTS_TABLE`, `LOGS_TABLE`, `JOBS_TABLE` | see defaults   | Override SQL table / index suffix names                     |
| `TIMEZONE`                                                  | `Asia/Karachi` | Timezone for `created_at`                                   |
| `JOB_ID`                                                    | auto           | Omit to auto-generate (`Rs_Spider-178826754-a1b2`)          |

## Troubleshooting

- **Password has `@` or `$` in `DB_URL`?** Encode them: `@` → `%40`, `$` → `%24`. Or use discrete `DB_*` fields.
- **Yield items** from callbacks (not only `return` inside a generator).
- **Elasticsearch / OpenSearch connection refused?** Check `SEARCH_URL`, firewall, and that the cluster is running. Test with `curl http://localhost:9200`.
- **HTTPS / self-signed cert?** Set `SEARCH_SSL_VERIFY = False` in development only.

## Standalone components

If you only want part of the collection:

```python
# Items only
ITEM_PIPELINES = {"scrapy_ingest.pipelines.ItemsPipeline": 300}

# Requests only (parent_url + errors)
ITEM_PIPELINES = {"scrapy_ingest.pipelines.RequestsPipeline": 300}

# Logs only
EXTENSIONS = {"scrapy_ingest.extensions.LoggingExtension": 500}
```

## Links

- Docs: https://scrapy-ingest.readthedocs.io/
- Changelog: [docs/development/changelog.rst](docs/development/changelog.rst)
- Issues: https://github.com/fawadss1/scrapy-ingest/issues

## License

MIT License. See [LICENSE](LICENSE).
