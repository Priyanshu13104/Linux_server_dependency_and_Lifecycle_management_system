from modules.service_monitor import status_summary, get_failed_services
from modules.dependency_manager import dependency_status
from database.operations import (
    recent_activity, recent_failures, recent_recovery_attempts, historical_summary,
)


def current_status_report():
    return status_summary()


def failed_services_report():
    return get_failed_services()


def dependency_health_report(service_names):
    return {
        service_name: dependency_status(service_name)
        for service_name in service_names
    }


def recent_operations_report(limit=50, db_path=None):
    return recent_activity(limit, db_path=db_path)


def recovery_report(limit=50, db_path=None):
    return recent_recovery_attempts(limit, db_path=db_path)


def historical_report(db_path=None):
    return {
        "counts": historical_summary(db_path=db_path),
        "activity": recent_activity(20, db_path=db_path),
        "failures": recent_failures(20, db_path=db_path),
        "recoveries": recent_recovery_attempts(20, db_path=db_path),
    }
