"""Shared batch collector for items, requests, logs, and stats."""

from .collector import DataCollector, ensure_collector

__all__ = ["DataCollector", "ensure_collector"]
