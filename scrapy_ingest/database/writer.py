"""Flush collector batches into PostgreSQL or MySQL tables."""
from ..utils.serialization import serialize_item_data
from ..utils.time import get_current_datetime


class DbWriter:
    """Insert a collector batch into items, requests, and logs tables."""

    def __init__(self, db, settings):
        self.db = db
        self.settings = settings

    def _is_mysql(self):
        return getattr(self.settings, "db_dialect", "postgres") == "mysql"

    def write(self, data, job_id):
        try:
            created_at = get_current_datetime(self.settings)
            self._write_items(data.get("items") or [], job_id, created_at)
            self._write_requests(data.get("requests") or [], job_id, created_at)
            self._write_logs(data.get("logs") or [], job_id)
            self.refresh_job_counts(job_id)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _upsert_job_sql(self, table):
        if self._is_mysql():
            return f"""
            INSERT INTO {table}
            (job_id, spider_name, status, started_at, items_count, requests_count,
             success_requests, failed_requests, errors_count, logs_count)
            VALUES (%s, %s, %s, %s, 0, 0, 0, 0, 0, 0)
            ON DUPLICATE KEY UPDATE
                spider_name = VALUES(spider_name),
                status = VALUES(status),
                started_at = VALUES(started_at),
                finished_at = NULL,
                finish_reason = NULL,
                items_count = 0,
                requests_count = 0,
                success_requests = 0,
                failed_requests = 0,
                errors_count = 0,
                logs_count = 0,
                elapsed_seconds = 0,
                items_per_min = 0,
                stats = NULL
            """
        return f"""
        INSERT INTO {table}
        (job_id, spider_name, status, started_at, items_count, requests_count,
         success_requests, failed_requests, errors_count, logs_count)
        VALUES (%s, %s, %s, %s, 0, 0, 0, 0, 0, 0)
        ON CONFLICT (job_id) DO UPDATE SET
            spider_name = EXCLUDED.spider_name,
            status = EXCLUDED.status,
            started_at = EXCLUDED.started_at,
            finished_at = NULL,
            finish_reason = NULL,
            items_count = 0,
            requests_count = 0,
            success_requests = 0,
            failed_requests = 0,
            errors_count = 0,
            logs_count = 0,
            elapsed_seconds = 0,
            items_per_min = 0,
            stats = NULL
        RETURNING id
        """

    def start_job(self, job_key, spider):
        """Insert or reset the jobs row. Returns the integer id."""
        started_at = get_current_datetime(self.settings)
        table = self.settings.db_jobs_table
        params = (job_key, getattr(spider, "name", None), "running", started_at)
        row = self.db.execute(self._upsert_job_sql(table), params)
        if self._is_mysql():
            row = self.db.execute(
                f"SELECT id FROM {table} WHERE job_id = %s", (job_key,)
            )
        self.db.commit()
        return int(row[0]) if row else None

    def _count(self, table, job_id, extra=""):
        sql = f"SELECT COUNT(*) FROM {table} WHERE job_id = %s {extra}"
        row = self.db.execute(sql, (job_id,))
        return int(row[0]) if row else 0

    def _job_counts(self, job_id):
        items = self._count(self.settings.db_items_table, job_id)
        requests = self._count(self.settings.db_requests_table, job_id)
        success = self._count(self.settings.db_requests_table, job_id, "AND success IS TRUE")
        failed = self._count(self.settings.db_requests_table, job_id, "AND success IS FALSE")
        logs = self._count(self.settings.db_logs_table, job_id)
        log_errors = self._count(
            self.settings.db_logs_table, job_id, "AND level IN ('ERROR', 'CRITICAL')"
        )
        return {
            "items_count": items,
            "requests_count": requests,
            "success_requests": success,
            "failed_requests": failed,
            "errors_count": failed + log_errors,
            "logs_count": logs,
        }

    @staticmethod
    def _naive(dt):
        if dt is None:
            return None
        if getattr(dt, "tzinfo", None) is not None:
            return dt.replace(tzinfo=None)
        return dt

    def _speed_metrics(self, job_id, items_count, end_time=None):
        """items per min from started_at → end_time."""
        row = self.db.execute(
            f"SELECT started_at FROM {self.settings.db_jobs_table} WHERE id = %s",
            (job_id,),
        )
        started_at = self._naive(row[0]) if row else None
        end = self._naive(end_time or get_current_datetime(self.settings))
        elapsed = 0.0
        if started_at is not None and end is not None:
            elapsed = max((end - started_at).total_seconds(), 0.0)
        if elapsed <= 0:
            return 0.0, 0.0
        return round(elapsed, 2), round(items_count / elapsed * 60, 2)

    def _update_job_metrics(self, job_id, extra_set="", extra_params=(), end_time=None):
        counts = self._job_counts(job_id)
        elapsed, items_per_min = self._speed_metrics(
            job_id, counts["items_count"], end_time=end_time
        )
        sql = f"""
        UPDATE {self.settings.db_jobs_table}
        SET {extra_set}
            items_count = %s,
            requests_count = %s,
            success_requests = %s,
            failed_requests = %s,
            errors_count = %s,
            logs_count = %s,
            elapsed_seconds = %s,
            items_per_min = %s
        WHERE id = %s
        """
        self.db.execute(
            sql,
            extra_params
            + (
                counts["items_count"],
                counts["requests_count"],
                counts["success_requests"],
                counts["failed_requests"],
                counts["errors_count"],
                counts["logs_count"],
                elapsed,
                items_per_min,
                job_id,
            ),
        )
        return {
            **counts,
            "elapsed_seconds": elapsed,
            "items_per_min": items_per_min,
        }

    def refresh_job_counts(self, job_id):
        """Update running totals and crawl speed on jobs."""
        self._update_job_metrics(job_id)

    def finish_job(self, job_id, reason=None, stats=None):
        """Mark the job finished and store full counts, speed, and Scrapy stats."""
        finished_at = get_current_datetime(self.settings)
        if stats and not reason:
            reason = stats.get("finish_reason")
        metrics = self._update_job_metrics(
            job_id,
            extra_set="status = %s, finished_at = %s, finish_reason = %s, stats = %s,",
            extra_params=(
                "finished",
                finished_at,
                reason,
                serialize_item_data(stats) if stats else None,
            ),
            end_time=finished_at,
        )
        self.db.commit()
        metrics["reason"] = reason
        return metrics

    def _write_items(self, items, job_id, created_at):
        if not items:
            return
        sql = (
            f"INSERT INTO {self.settings.db_items_table} "
            f"(job_id, item, created_at) VALUES (%s, %s, %s)"
        )
        rows = [(job_id, serialize_item_data(item), created_at) for item in items]
        self.db.executemany(sql, rows)

    def _write_requests(self, requests, job_id, created_at):
        if not requests:
            return
        sql = f"""
        INSERT INTO {self.settings.db_requests_table}
        (job_id, url, method, status_code, response_time_secs, fingerprint,
         parent_url, error, success, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        rows = [
            (
                job_id,
                req.get("url"),
                req.get("method"),
                req.get("status_code"),
                req.get("response_time_secs"),
                req.get("fingerprint"),
                req.get("parent_url"),
                req.get("error"),
                req.get("success"),
                created_at,
            )
            for req in requests
        ]
        self.db.executemany(sql, rows)
        self._link_parent_ids(job_id)

    def _link_parent_sql(self, table):
        """Resolve parent_id from parent_url. MySQL cannot UPDATE the same table it reads."""
        if self._is_mysql():
            return f"""
            UPDATE {table} AS child
            INNER JOIN (
                SELECT c.id AS child_id, MIN(p.id) AS parent_pk
                FROM {table} AS c
                INNER JOIN {table} AS p
                  ON p.job_id = c.job_id
                 AND p.url = c.parent_url
                 AND p.id <> c.id
                WHERE c.job_id = %s
                  AND c.parent_id IS NULL
                  AND c.parent_url IS NOT NULL
                GROUP BY c.id
            ) AS mapped ON child.id = mapped.child_id
            SET child.parent_id = mapped.parent_pk
            """
        return f"""
        UPDATE {table} AS child
        SET parent_id = (
            SELECT parent.id
            FROM {table} AS parent
            WHERE parent.job_id = child.job_id
              AND parent.url = child.parent_url
              AND parent.id <> child.id
            ORDER BY parent.id ASC
            LIMIT 1
        )
        WHERE child.job_id = %s
          AND child.parent_id IS NULL
          AND child.parent_url IS NOT NULL
        """

    def _link_parent_ids(self, job_id):
        """Set parent_id from parent_url → the earlier request with that URL."""
        self.db.execute(
            self._link_parent_sql(self.settings.db_requests_table), (job_id,)
        )

    def _write_logs(self, logs, job_id):
        if not logs:
            return
        time_col = "`time`" if self._is_mysql() else "time"
        sql = f"""
        INSERT INTO {self.settings.db_logs_table}
        (job_id, {time_col}, level, logger, message, exception)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        rows = [
            (
                job_id,
                entry.get("time"),
                entry.get("level"),
                entry.get("logger"),
                entry.get("message"),
                entry.get("exception"),
            )
            for entry in logs
        ]
        self.db.executemany(sql, rows)
