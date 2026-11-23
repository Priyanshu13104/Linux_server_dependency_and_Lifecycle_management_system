from modules import service_monitor


def test_status_summary(monkeypatch):
    monkeypatch.setattr(service_monitor, "list_services", lambda: [
        {"active": "active"}, {"active": "inactive"},
        {"active": "failed"}, {"active": "activating"},
    ])
    assert service_monitor.status_summary() == {
        "active": 1, "inactive": 1, "failed": 1, "other": 1,
    }


def test_get_service_status(monkeypatch):
    monkeypatch.setattr(service_monitor, "execute", lambda command: {
        "success": True,
        "stdout": "LoadState=loaded\nActiveState=active\nSubState=running\nUnitFileState=enabled\n",
        "stderr": "",
        "returncode": 0,
    })
    status = service_monitor.get_service_status("ssh.service")
    assert status["active"] == "active"
    assert status["enabled"] == "enabled"


def test_invalid_service_name():
    assert service_monitor.get_service_status("../../bin")["success"] is False
