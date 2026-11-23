from modules import failure_detector


def test_periodic_check_only_failed(monkeypatch):
    monkeypatch.setattr(failure_detector, "get_service_status", lambda name: {
        "success": True, "active": "inactive",
    })
    monkeypatch.setattr(failure_detector, "detect_dependency_failures", lambda name, db_path=None: [])
    assert failure_detector.periodic_check(["test.service"]) == []


def test_detect_failed_services(monkeypatch, tmp_path):
    monkeypatch.setattr(failure_detector, "get_failed_services",
                        lambda: [{"name": "broken.service"}])
    monkeypatch.setattr(failure_detector, "get_service_status",
                        lambda name: {"success": True, "active": "failed", "sub": "failed"})
    monkeypatch.setattr(failure_detector, "get_recent_journal", lambda name, lines: "boom")
    monkeypatch.setattr(failure_detector, "save_failure", lambda *args, **kwargs: None)
    result = failure_detector.detect_failed_services(db_path=tmp_path / "test.db")
    assert result[0]["name"] == "broken.service"
