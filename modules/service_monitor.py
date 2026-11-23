from utils.command_executor import execute
from utils.validators import validate_service_name


def list_services(include_not_found=False):
    result = execute([
        "systemctl", "--no-pager", "--plain", "list-units",
        "--type=service", "--all",
    ])
    if not result["success"]:
        return []
    services = []
    for line in result["stdout"].splitlines():
        parts = line.split(None, 4)
        if len(parts) < 4 or not parts[0].endswith(".service"):
            continue
        name, load, active, sub = parts[:4]
        if not include_not_found and load == "not-found":
            continue
        services.append({
            "name": name,
            "load": load,
            "active": active,
            "sub": sub,
            "description": parts[4] if len(parts) > 4 else "",
        })
    return services


def get_service_status(service_name):
    if not validate_service_name(service_name):
        return {"success": False, "error": "Invalid service name."}
    result = execute([
        "systemctl", "show", service_name, "--no-pager",
        "-p", "LoadState", "-p", "ActiveState", "-p", "SubState",
        "-p", "UnitFileState", "-p", "FragmentPath", "-p", "Description",
    ])
    if not result["success"]:
        return {
            "success": False,
            "name": service_name,
            "error": result["stderr"].strip() or "Unable to inspect service.",
        }
    properties = {}
    for line in result["stdout"].splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            properties[key] = value
    return {
        "success": True,
        "name": service_name,
        "load": properties.get("LoadState", "unknown"),
        "active": properties.get("ActiveState", "unknown"),
        "sub": properties.get("SubState", "unknown"),
        "enabled": properties.get("UnitFileState", "unknown"),
        "fragment": properties.get("FragmentPath", ""),
        "description": properties.get("Description", ""),
    }


def get_running_services():
    return [service for service in list_services() if service["active"] == "active"]


def get_failed_services():
    return [service for service in list_services(True) if service["active"] == "failed"]


def get_enablement_state(service_name):
    status = get_service_status(service_name)
    if not status["success"]:
        return {"success": False, "enabled": "unknown", "error": status["error"]}
    return {"success": True, "enabled": status["enabled"]}


def status_summary():
    summary = {"active": 0, "inactive": 0, "failed": 0, "other": 0}
    for service in list_services():
        active = service["active"]
        if active in ("active", "inactive", "failed"):
            summary[active] += 1
        else:
            summary["other"] += 1
    return summary
