"""User-facing notices that always show and are not stored in job_logs."""

import sys
import threading

_lock = threading.Lock()


def info(message):
    """Print *message* to stderr so it is visible at any LOG_LEVEL."""
    with _lock:
        print(message, file=sys.stderr, flush=True)


def format_table(headers, rows):
    """Return an ASCII table for *headers* and *rows*."""
    headers = [str(cell) for cell in headers]
    rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(cell) for cell in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def border():
        return "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def line(cells):
        return (
            "| "
            + " | ".join(cell.ljust(width) for cell, width in zip(cells, widths))
            + " |"
        )

    parts = [border(), line(headers), border()]
    parts.extend(line(row) for row in rows)
    parts.append(border())
    return "\n".join(parts)
