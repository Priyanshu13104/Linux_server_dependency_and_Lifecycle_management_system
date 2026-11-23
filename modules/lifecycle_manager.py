from database.operations import save_activity
from modules.log_manager import record_activity
from modules.service_monitor import get_service_status
from utils.command_executor import execute
from utils.validators import validate_service_name, validate_operation


def perform_lifecycle_operation(service_name, operation, db_path=None, log_path=None):
    operation = operation.lower() if isinstance(operation, str) else ""
    if not validate_service_name(service_name):
        return {"success": False, "error": "Invalid service name."}
    if not validate_operation(operation):
        return {"success": False, "error": "Invalid lifecycle operation."}

    before = get_service_status(service_name)
    if not before["success"]:
        record_activity(
            service_name, operation, None, None, "failed",
            before["error"], db_path=db_path, log_path=log_path,
        )
        return before

    result = execute(["systemctl", operation, service_name])
    after = get_service_status(service_name)
    if not result["success"]:
        error = result["stderr"].strip() or "systemctl returned a nonzero status."
        record_activity(
            service_name, operation, before["active"], after.get("active"),
            "failed", error, db_path=db_path, log_path=log_path,
        )
        return {"success": False, "error": error, "before": before, "after": after}

    operation_success = True
    if operation == "start":
        operation_success = after.get("active") == "active"
    elif operation == "stop":
        operation_success = after.get("active") in ("inactive", "failed")
    elif operation == "restart":
        operation_success = after.get("active") == "active"
    elif operation == "reload":
        operation_success = after.get("active") == "active"
    elif operation == "enable":
        operation_success = after.get("enabled") in ("enabled", "enabled-runtime", "static")
    elif operation == "disable":
        operation_success = after.get("enabled") in ("disabled", "masked")

    outcome = "success" if operation_success else "failed"
    error = None if operation_success else "State did not change as expected after systemctl returned success."
    record_activity(
        service_name, operation, before["active"], after.get("active"),
        outcome, error, db_path=db_path, log_path=log_path,
    )
    return {
        "success": operation_success,
        "message": "Operation completed and resulting state was verified."
        if operation_success else "Command ran but resulting state could not be verified.",
        "before": before,
        "after": after,
        "error": error,
        "command_output": result["stdout"].strip(),
    }
