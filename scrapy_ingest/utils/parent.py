"""Crawl-graph parent URL helpers."""


from .fingerprint import get_request_fingerprint


def get_parent_url(request, crawler=None):
    """
    URL of the page/response that scheduled this request.

    Reads request.meta['parent_url'] first, then the fingerprint map
    (survives meta loss from replace/middleware). Start URLs return None.
    """
    parent = request.meta.get("parent_url")
    if parent:
        return parent
    if crawler is not None:
        by_fp = getattr(crawler, "ingest_parent_by_fp", None) or {}
        return by_fp.get(get_request_fingerprint(request))
    return None


def set_parent_url(request, parent_url, crawler=None):
    """Stamp parent on the request and remember it by fingerprint."""
    if not parent_url:
        return
    request.meta.setdefault("parent_url", parent_url)
    if crawler is not None:
        if not hasattr(crawler, "ingest_parent_by_fp"):
            crawler.ingest_parent_by_fp = {}
        crawler.ingest_parent_by_fp[get_request_fingerprint(request)] = parent_url
