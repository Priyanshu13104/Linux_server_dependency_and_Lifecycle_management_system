from modules.dependency_manager import unhealthy_dependencies
from modules.service_monitor import get_failed_services, get_service_status
from database.operations import save_failure
from utils.command_executor import execute
from utils.validators import validate_service_name


def get_recent_journal(service_name, lines=20):
    if not validate_service_name(service_name):
        return ""
    result = execute([
        "journalctl", "--no-pager", "-n", str(lines),
        "-u", service_name,
    ])
    return result["stdout"] if result["success"] else result["stderr"]


def detect_failed_services(db_path=None):
    failures = []
    for service in get_failed_services():
        status = get_service_status(service["name"])
        details = get_recent_journal(service["name"], 10)
        record = {
            "name": service["name"],
            "type": "failed",
            "details": details[-2000:],
            "active": status.get("active", "failed"),
            "sub": status.get("sub", "unknown"),
        }
        failures.append(record)
        save_failure(
            service["name"], "failed", record["details"],
            record["active"], record["sub"], db_path=db_path,
        )
    return failures


def detect_dependency_failures(service_name, db_path=None):
    if not validate_service_name(service_name):
        return []
    unhealthy = unhealthy_dependencies(service_name)
    for item in unhealthy:
        save_failure(
            service_name,
            "dependency_failure",
            f"Dependency {item['dependency']} is unhealthy "
            f"(relationship={item['property']}, state={item['status']})",
            db_path=db_path,
        )
    return unhealthy


def periodic_check(service_names, db_path=None):
    detected = []
    for service_name in service_names:
        if not validate_service_name(service_name):
            continue
        status = get_service_status(service_name)
        if status.get("active") == "failed":
            detected.append({
                "name": service_name,
                "status": status,
                "dependency_failures": detect_dependency_failures(service_name, db_path),
            })
    return detected
