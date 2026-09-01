import sys
from unittest.mock import patch

from scrapy_ingest.utils.console import format_table, info


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
