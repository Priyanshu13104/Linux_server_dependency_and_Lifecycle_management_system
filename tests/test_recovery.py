from modules.auto_recovery import RecoveryController
from utils.validators import validate_recovery_policy


def test_recovery_policy_validation():
    policy = {
        "automatic_recovery_enabled": True,
        "recovery_allowlist": ["test.service"],
        "recovery_retry_limit": 3,
        "recovery_cooldown": 300,
    }
    assert validate_recovery_policy(policy)


def test_recovery_disabled(tmp_path):
    policy = {
        "automatic_recovery_enabled": False,
        "recovery_allowlist": ["test.service"],
        "recovery_retry_limit": 3,
        "recovery_cooldown": 300,
    }
    controller = RecoveryController(policy, db_path=tmp_path / "test.db")
    result = controller.recover("test.service")
    assert result["success"] is False
