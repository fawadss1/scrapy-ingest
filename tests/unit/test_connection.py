from unittest.mock import MagicMock, patch

from scrapy_ingest.database.connection import DBConnection


def _mock_pg_connection():
    return MagicMock(closed=0)


class TestDBConnection:
    def setup_method(self):
        DBConnection._instance = None

    def teardown_method(self):
        DBConnection._instance = None

    def test_postgres_sets_application_name(self):
        with patch("psycopg2.connect", return_value=_mock_pg_connection()) as mock_connect:
            DBConnection("postgresql://user:pass@localhost:5432/db")

        mock_connect.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/db",
            application_name="Ingest",
        )

    def test_postgres_application_name_overrides_dsn_default(self):
        conn = object.__new__(DBConnection)
        with patch("psycopg2.connect", return_value=_mock_pg_connection()) as mock_connect:
            conn._connect_postgres(
                "postgresql://user:pass@localhost:5432/db?application_name=other",
            )

        mock_connect.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/db?application_name=other",
            application_name="Ingest",
        )
