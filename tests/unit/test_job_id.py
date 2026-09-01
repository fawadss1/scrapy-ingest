from unittest.mock import patch

from scrapy_ingest.utils.job_id import generate_job_id


def test_generate_job_id_uses_unix_time_and_is_unique():
    with patch("scrapy_ingest.utils.job_id.time.time", return_value=178826754.9):
        first = generate_job_id("Rs_Spider")
        second = generate_job_id("Rs_Spider")

    assert first.startswith("Rs_Spider-178826754-")
    assert second.startswith("Rs_Spider-178826754-")
    assert first != second
    assert len(first.split("-")[-1]) == 6
