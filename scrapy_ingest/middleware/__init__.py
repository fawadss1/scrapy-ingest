"""Downloader middleware and parent_url scraper hooks."""

from .middleware import ErrorMiddleware, install_parent_url_tracking, _inject_into_scraper

__all__ = ["ErrorMiddleware", "install_parent_url_tracking", "_inject_into_scraper"]
