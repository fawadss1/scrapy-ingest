import sys
from unittest.mock import patch

from scrapy_ingest.utils.console import format_labeled_grid, format_pair_grid, format_table, info


def test_info_prints_to_stderr():
    with patch("scrapy_ingest.utils.console.print") as mock_print:
        info("hello")

    mock_print.assert_called_once_with("hello", file=sys.stderr, flush=True)


def test_format_table_aligns_columns():
    text = format_table(("Metric", "Count"), (("items", 120), ("logs", 3)))
    assert text.splitlines()[0].startswith("+")
    assert "| Metric |" in text
    assert "| items  | 120   |" in text
    assert "| logs   | 3     |" in text
    assert text.endswith("+--------+-------+")


def test_format_pair_grid_uses_two_pairs_per_row():
    text = format_pair_grid((("job", "j1"), ("spider", "demo"), ("status", "ok")))
    lines = text.splitlines()
    assert "| job " in lines[1] and "| spider " in lines[1]
    assert "| status " in lines[2] and "| ok " in lines[2]
    assert "Field" not in text


def test_format_labeled_grid_uses_four_columns():
    text = format_labeled_grid(
        (("job", "j1"), ("spider", "demo"), ("status", "ok"), ("items", "3"), ("logs", "1")),
        cols=4,
    )
    lines = text.splitlines()
    assert "| job " in lines[1] and "| spider " in lines[1] and "| status " in lines[1]
    assert "| j1 " in lines[2] and "| demo " in lines[2]
    assert "| logs " in lines[3] and "| 1 " in lines[4]
