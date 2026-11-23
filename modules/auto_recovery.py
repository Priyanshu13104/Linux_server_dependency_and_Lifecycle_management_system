import time

from config import CRITICAL_SERVICES
from database.operations import save_recovery_attempt
from modules.dependency_manager import unhealthy_dependencies
from modules.lifecycle_manager import perform_lifecycle_operation
from modules.log_manager import record_activity
from modules.service_monitor import get_service_status
from utils.validators import validate_recovery_policy


class RecoveryController:
    def __init__(self, policy, db_path=None, log_path=None):
        self.policy = policy
        self.db_path = db_path
        self.log_path = log_path
        self.attempt_counts = {}
        self.last_attempt = {}

    def recover(self, service_name):
        if not validate_recovery_policy(self.policy):
            return {"success": False, "error": "Invalid recovery policy."}
        if not self.policy["automatic_recovery_enabled"]:
            return {"success": False, "error": "Automatic recovery is disabled."}
        if service_name not in self.policy["recovery_allowlist"]:
            return {"success": False, "error": "Service is not in the recovery allowlist."}
        service_base = service_name.removesuffix(".service")
        if any(service_base == name or service_base.startswith(name + ".") for name in CRITICAL_SERVICES):
            return {"success": False, "error": "Critical system services are protected from automatic recovery."}

        status = get_service_status(service_name)
        if status.get("active") != "failed":
            return {"success": False, "error": "Service is not currently failed."}
        if unhealthy_dependencies(service_name):
            return {"success": False, "error": "Recovery skipped because a requirement dependency is unhealthy."}

        attempts = self.attempt_counts.get(service_name, 0)
        limit = self.policy["recovery_retry_limit"]
        if attempts >= limit:
            return {"success": False, "error": "Recovery retry limit reached."}

        now = time.monotonic()
        previous_attempt = self.last_attempt.get(service_name)
        cooldown = self.policy["recovery_cooldown"]
        if previous_attempt is not None and now - previous_attempt < cooldown:
            return {"success": False, "error": "Recovery cooldown is still active."}

        attempt_number = attempts + 1
        before = status
        operation = perform_lifecycle_operation(
            service_name, "restart",
            db_path=self.db_path, log_path=self.log_path,
        )
        after = operation.get("after", {})
        result = "success" if operation["success"] else "failed"
        details = operation.get("error")

        self.attempt_counts[service_name] = attempt_number
        self.last_attempt[service_name] = now
        save_recovery_attempt(
            service_name, attempt_number, result,
            before.get("active"), after.get("active"),
            details, db_path=self.db_path,
        )
        record_activity(
            service_name, "auto-restart", before.get("active"),
            after.get("active"), result, details,
            db_path=self.db_path, log_path=self.log_path,
        )
        return {
            "success": operation["success"],
            "attempt": attempt_number,
            "before": before,
            "after": after,
            "error": details,
        }
