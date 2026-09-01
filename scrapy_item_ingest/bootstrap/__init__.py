"""Bootstrap helpers that auto-enable ingest components."""

from .bootstrap import attach_runtime_hooks, enable_ingest

__all__ = ["attach_runtime_hooks", "enable_ingest"]
