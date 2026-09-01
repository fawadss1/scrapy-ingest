"""Unique job_id generation when the user does not set JOB_ID."""

import time
import uuid


def generate_job_id(spider_name):
    """Return a unique id like ``Rs_Spider-178826754-a1b2``."""
    return f"{spider_name}-{int(time.time())}-{uuid.uuid4().hex[:4]}"


def cache_job_id(spider, job_id):
    """Remember the resolved job_id on spider and crawler."""
    spider._ingest_job_id = job_id
    crawler = getattr(spider, "crawler", None)
    if crawler is not None:
        crawler.ingest_job_id = job_id
    return job_id


def cached_job_id(spider):
    crawler = getattr(spider, "crawler", None)
    if crawler is not None:
        existing = getattr(crawler, "ingest_job_id", None)
        if existing:
            return existing
    return getattr(spider, "_ingest_job_id", None)
