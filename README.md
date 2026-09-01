# Scrapy Ingest

A Scrapy addon that saves **items, requests, logs, and stats** to PostgreSQL — with parent_url tracking, failed-request errors, and full job log capture (including `print()`).

## Install

```bash
pip install scrapy-ingest
```

## Minimal setup (settings.py)

Only the item pipeline is required — requests, logs, stats, parent_url, and error logging are enabled automatically:

```python
ITEM_PIPELINES = {
    "scrapy_ingest.pipelines.DbInsertPipeline": 300,
}

# Pick ONE of the two database config styles:
DB_URL = "postgresql://user:password@localhost:5432/database"
# Or use discrete fields (avoids URL encoding):
# DB_TYPE = "postgres"
# DB_HOST = "localhost"
# DB_PORT = 5432
# DB_USER = "user"
# DB_PASSWORD = "password"
# DB_NAME = "database"

# Optional
CREATE_TABLES = True     # auto-create tables on first run (default True)
JOB_ID = 1               # or omit; a unique id is generated per crawl
INGEST_BATCH_SIZE = 50   # flush when this many rows are buffered
```

Run your spider:

```bash
scrapy crawl your_spider
```

Log level follows Scrapy `LOG_LEVEL`.

## What is stored

| Table          | Contents                                                                                                |
|----------------|---------------------------------------------------------------------------------------------------------|
| `jobs`         | One row per crawl: `id`, unique `job_id` string, spider, status, start/finish, counts, items/min, stats |
| `job_items`    | JSON items (`crawled_at` added). `job_id` = `jobs.id` (CASCADE)                                         |
| `job_requests` | url, parent_url, parent_id, status, response_time, error, success. `job_id` = `jobs.id` (CASCADE)       |
| `job_logs`     | time, logger, level, message, exception. `job_id` = `jobs.id` (CASCADE)                                 |

Request `parent_url` is the page that scheduled the request (e.g. sitemap → product). Start URLs are `null`.

Data flushes on batch size, every 10s, and on engine/process stop.

When the spider closes, a crawl summary is printed (job, database, tables, items, requests, logs, errors, elapsed time) even if `LOG_LEVEL` is `ERROR`. Set `INGEST_SHOW_SUMMARY = False` to hide it.

## Troubleshooting

- Password has special characters like `@` or `$`?
  - In a URL, encode them: `@` -> `%40`, `$` -> `%24`.
  - Example: `postgresql://user:PAK%40swat1%24@localhost:5432/db`
  - Or use the discrete fields (no encoding needed).
- **Yield items** from callbacks (not only `return` inside a generator).

## Useful settings (optional)

- `DB_TYPE` (default: `postgres`) — used when building a URL from `DB_HOST` / `DB_*` fields
- `INGEST_BATCH_SIZE` (default: `50`) — flush when this many items+requests+logs are buffered
- `INGEST_FLUSH_INTERVAL` (default: `10`) — periodic flush in seconds
- `INGEST_SHOW_SUMMARY` (default: `True`) — print crawl summary tables when the spider closes
- `CREATE_TABLES` (default: `True`) — create tables on startup
- `ITEMS_TABLE`, `REQUESTS_TABLE`, `LOGS_TABLE`, `JOBS_TABLE` — override table names
- `TIMEZONE` (default: `Asia/Karachi`) — timezone for `created_at`
- `JOB_ID` — omit to auto-generate a unique id (`spider-YYYYMMDDHHMMSS-xxxxxxxx`)

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
- Changelog: docs/development/changelog.rst
- Issues: https://github.com/fawadss1/scrapy_item_ingest/issues

## License

MIT License. See [LICENSE](LICENSE).
