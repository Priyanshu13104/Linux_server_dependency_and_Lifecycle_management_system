from utils import command_executor


def test_missing_command(monkeypatch):
    monkeypatch.setattr(command_executor.shutil, "which", lambda name: None)
    result = command_executor.execute(["does-not-exist"])
    assert result["success"] is False
    assert "Command not found" in result["stderr"]


def test_timeout(monkeypatch):
    monkeypatch.setattr(command_executor.shutil, "which", lambda name: "/bin/true")
    def timeout(*args, **kwargs):
        raise command_executor.subprocess.TimeoutExpired("true", 1)
    monkeypatch.setattr(command_executor.subprocess, "run", timeout)
    result = command_executor.execute(["true"], timeout=1)
    assert result["success"] is False
    assert result["stderr"] == "Command timed out."
