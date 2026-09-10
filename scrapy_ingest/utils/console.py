"""User-facing notices that always show and are not stored in job_logs."""

import sys
import threading

_lock = threading.Lock()


def info(message):
    """Print *message* to stderr so it is visible at any LOG_LEVEL."""
    with _lock:
        print(message, file=sys.stderr, flush=True)


def format_table(headers, rows, *, header=True):
    """Return an ASCII table for *headers* and *rows*."""
    headers = [str(cell) for cell in headers]
    rows = [[str(cell) for cell in row] for row in rows]
    if not rows:
        return ""

    ncol = max(len(headers), max(len(row) for row in rows))
    widths = [0] * ncol
    if header:
        for i, cell in enumerate(headers):
            widths[i] = len(cell)
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def border():
        return "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def line(cells):
        padded = cells + [""] * (ncol - len(cells))
        return (
            "| "
            + " | ".join(cell.ljust(width) for cell, width in zip(padded, widths))
            + " |"
        )

    parts = [border()]
    if header:
        parts.extend((line(headers), border()))
    parts.extend(line(row) for row in rows)
    parts.append(border())
    return "\n".join(parts)


def format_pair_grid(pairs, pairs_per_row=2):
    """Format ``(label, value)`` pairs in a compact multi-column grid."""
    cols = pairs_per_row * 2
    rows = []
    batch = []
    for label, value in pairs:
        batch.extend((label, value))
        if len(batch) == cols:
            rows.append(batch)
            batch = []
    if batch:
        batch.extend(("", "") * ((cols - len(batch)) // 2))
        rows.append(batch)
    return format_table(("",) * cols, rows, header=False)


def format_labeled_grid(pairs, cols=4):
    """Format pairs as *cols* columns: label row, then value row, repeated."""
    rows = []
    for i in range(0, len(pairs), cols):
        chunk = list(pairs[i : i + cols])
        while len(chunk) < cols:
            chunk.append(("", ""))
        rows.append([label for label, _ in chunk])
        rows.append([value for _, value in chunk])
    return format_table(("",) * cols, rows, header=False)
