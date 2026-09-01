"""Thread-safe batch buffer for requests, items, logs, and stats."""
from threading import Lock


def ensure_collector(crawler):
    """Return the crawler's shared DataCollector, creating it if needed."""
    if not hasattr(crawler, "ingest_collector"):
        crawler.ingest_collector = DataCollector()
    return crawler.ingest_collector


class DataCollector:
    """
    Collects requests, items, logs, and stats in batches.

    Thread-safe. One instance is stored on the crawler and shared by the
    pipeline, request logger, error middleware, and logging extension.
    """

    def __init__(self):
        self.requests = []
        self.items = []
        self.logs = []
        self.stats = None
        self.lock = Lock()

    def add_request(self, request_log: dict):
        with self.lock:
            self.requests.append(request_log)

    def add_item(self, item: dict):
        with self.lock:
            self.items.append(item)

    def add_log(self, log_entry: dict):
        with self.lock:
            self.logs.append(log_entry)

    def set_stats(self, stats: dict):
        with self.lock:
            self.stats = stats

    def get_and_clear(self):
        """Return collected data and clear buffers. None if empty."""
        with self.lock:
            if not (self.requests or self.items or self.logs or self.stats):
                return None

            data = {
                "requests": self.requests[:],
                "items": self.items[:],
                "logs": self.logs[:],
            }
            if self.stats:
                data["stats"] = self.stats

            self.requests.clear()
            self.items.clear()
            self.logs.clear()
            self.stats = None
            return data

    def requeue(self, data: dict):
        """Put data back at the front of the buffers after a failed flush."""
        with self.lock:
            self.requests = data.get("requests", []) + self.requests
            self.items = data.get("items", []) + self.items
            self.logs = data.get("logs", []) + self.logs
            if data.get("stats") is not None and self.stats is None:
                self.stats = data["stats"]

    def has_data(self) -> bool:
        with self.lock:
            return bool(self.requests or self.items or self.logs or self.stats)

    def size(self) -> int:
        with self.lock:
            return len(self.requests) + len(self.items) + len(self.logs)
