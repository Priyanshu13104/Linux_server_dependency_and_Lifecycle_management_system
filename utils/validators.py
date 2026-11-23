import re


SERVICE_PATTERN = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")
OPERATIONS = {"start", "stop", "restart", "reload", "enable", "disable"}


def validate_service_name(name):
    if not isinstance(name, str):
        return False
    name = name.strip()
    return bool(name) and bool(SERVICE_PATTERN.fullmatch(name))


def validate_operation(operation):
    return isinstance(operation, str) and operation.lower() in OPERATIONS


def validate_service_list(names):
    return isinstance(names, list) and all(validate_service_name(name) for name in names)


def validate_recovery_policy(policy):
    if not isinstance(policy, dict):
        return False
    required = {"automatic_recovery_enabled", "recovery_allowlist",
                "recovery_retry_limit", "recovery_cooldown"}
    if not required.issubset(policy):
        return False
    if not isinstance(policy["automatic_recovery_enabled"], bool):
        return False
    if not isinstance(policy["recovery_allowlist"], list):
        return False
    if not validate_service_list(policy["recovery_allowlist"]):
        return False
    return (
        isinstance(policy["recovery_retry_limit"], int)
        and policy["recovery_retry_limit"] > 0
        and isinstance(policy["recovery_cooldown"], (int, float))
        and policy["recovery_cooldown"] >= 0
    )
