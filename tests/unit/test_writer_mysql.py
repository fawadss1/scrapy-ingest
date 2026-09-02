from unittest.mock import MagicMock

from scrapy_ingest.database.writer import DbWriter


def test_start_job_mysql_selects_id_after_upsert():
    settings = MagicMock()
    settings.db_jobs_table = "jobs"
    settings.db_dialect = "mysql"
    settings.get_tz.return_value = "UTC"
    db = MagicMock()
    db.execute.side_effect = [None, (42,)]

    writer = DbWriter(db, settings)
    spider = MagicMock()
    spider.name = "quotes"

    job_pk = writer.start_job("quotes-1", spider)

    assert job_pk == 42
    assert db.execute.call_count == 2
    first_sql = db.execute.call_args_list[0].args[0]
    assert "ON DUPLICATE KEY UPDATE" in first_sql
    second_sql = db.execute.call_args_list[1].args[0]
    assert "SELECT id FROM jobs" in second_sql
