from modules import lifecycle_manager


def test_lifecycle_success(monkeypatch, tmp_path):
    before = {"success": True, "active": "inactive", "enabled": "disabled"}
    after = {"success": True, "active": "active", "enabled": "enabled"}
    calls = {"count": 0}
    def status(name):
        calls["count"] += 1
        return before if calls["count"] == 1 else after
    monkeypatch.setattr(lifecycle_manager, "get_service_status", status)
    monkeypatch.setattr(lifecycle_manager, "execute", lambda command: {
        "success": True, "stdout": "", "stderr": "", "returncode": 0,
    })
    monkeypatch.setattr(lifecycle_manager, "record_activity", lambda *args, **kwargs: None)
    result = lifecycle_manager.perform_lifecycle_operation(
        "test.service", "start", db_path=tmp_path / "test.db",
    )
    assert result["success"] is True


def test_lifecycle_rejects_invalid_operation():
    result = lifecycle_manager.perform_lifecycle_operation("test.service", "rm")
    assert result["success"] is False
