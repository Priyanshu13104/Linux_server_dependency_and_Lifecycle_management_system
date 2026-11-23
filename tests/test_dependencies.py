from modules import dependency_manager


def test_dependency_classification(monkeypatch):
    monkeypatch.setattr(dependency_manager, "execute", lambda command: {
        "success": True,
        "stdout": "Requires=network.target\nWants=ssh.service\nAfter=basic.target\n",
        "stderr": "",
        "returncode": 0,
    })
    relationships = dependency_manager.get_unit_dependencies("test.service")
    types = {item["property"]: item["type"] for item in relationships}
    assert types["Requires"] == "requirement"
    assert types["Wants"] == "optional"
    assert types["After"] == "ordering"
