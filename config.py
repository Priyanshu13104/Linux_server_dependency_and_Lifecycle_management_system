from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
MONITORING_INTERVAL = 10
RECOVERY_RETRY_LIMIT = 3
RECOVERY_COOLDOWN = 300
COMMAND_TIMEOUT = 15
DATABASE_PATH = BASE_DIR / "data" / "service_manager.db"
LOG_FILE_PATH = BASE_DIR / "logs" / "activity.log"
MONITORING_CONFIG_PATH = BASE_DIR / "config" / "monitoring.json"
CRITICAL_SERVICES = {
    "systemd", "dbus", "systemd-journald", "systemd-logind",
    "NetworkManager", "networking", "ssh", "sshd",
}

DEFAULT_MONITORING_CONFIG = {
    "monitoring_interval": MONITORING_INTERVAL,
    "services": [],
    "automatic_recovery_enabled": False,
    "recovery_allowlist": [],
    "recovery_retry_limit": RECOVERY_RETRY_LIMIT,
    "recovery_cooldown": RECOVERY_COOLDOWN,
}


def load_monitoring_config(path=None):
    config_path = Path(path or MONITORING_CONFIG_PATH)
    if not config_path.exists():
        return dict(DEFAULT_MONITORING_CONFIG)
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate_monitoring_config(data)
    return data


def save_monitoring_config(data, path=None):
    validate_monitoring_config(data)
    config_path = Path(path or MONITORING_CONFIG_PATH)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def validate_monitoring_config(data):
    if not isinstance(data, dict):
        raise ValueError("Monitoring configuration must be a JSON object.")
    interval = data.get("monitoring_interval", MONITORING_INTERVAL)
    limit = data.get("recovery_retry_limit", RECOVERY_RETRY_LIMIT)
    cooldown = data.get("recovery_cooldown", RECOVERY_COOLDOWN)
    if not isinstance(interval, int) or interval <= 0:
        raise ValueError("monitoring_interval must be a positive integer.")
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("recovery_retry_limit must be a positive integer.")
    if not isinstance(cooldown, (int, float)) or cooldown < 0:
        raise ValueError("recovery_cooldown must be zero or greater.")
    if not isinstance(data.get("services", []), list):
        raise ValueError("services must be a list.")
    if not isinstance(data.get("recovery_allowlist", []), list):
        raise ValueError("recovery_allowlist must be a list.")
    if not isinstance(data.get("automatic_recovery_enabled", False), bool):
        raise ValueError("automatic_recovery_enabled must be true or false.")
    return True
