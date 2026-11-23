from database.connection import initialize_database
from database.operations import (
    save_activity, recent_activity, historical_summary,
)


def test_database_operations(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path)
    save_activity("test.service", "start", "inactive", "active",
                  "success", db_path=db_path)
    records = recent_activity(db_path=db_path)
    assert records[0]["operation"] == "start"
    summary = historical_summary(db_path=db_path)
    assert summary["service_activity"] == 1
