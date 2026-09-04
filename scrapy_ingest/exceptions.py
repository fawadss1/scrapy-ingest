"""Exception types for scrapy-ingest."""


class IngestError(Exception):
    """Base class for scrapy-ingest errors."""


class ConfigurationError(IngestError):
    """Invalid or incomplete ingest configuration."""


class DependencyError(IngestError):
    """A required driver package is not installed."""


class IngestConnectionError(IngestError):
    """Failed to connect to the database or search cluster."""


class DatabaseError(IngestError):
    """A database operation failed."""


class SchemaError(DatabaseError):
    """Failed to create or verify database tables."""


class SearchError(IngestError):
    """A search index operation failed."""


class FlushError(IngestError):
    """Failed to flush a collector batch to a destination."""
