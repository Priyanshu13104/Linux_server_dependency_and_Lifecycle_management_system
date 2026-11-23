from modules import log_manager


def test_record_activity(monkeypatch, tmp_path):
    monkeypatch.setattr(log_manager, "save_activity", lambda *args, **kwargs: None)
    log_manager.record_activity(
        "test.service", "start", "inactive", "active", "success",
        db_path=tmp_path / "test.db", log_path=tmp_path / "activity.log",
    )
    assert (tmp_path / "activity.log").exists()
