import sys
import json
import time

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

import config
from database.connection import initialize_database
from modules.service_monitor import (
    list_services, get_service_status, status_summary,
)
from modules.lifecycle_manager import perform_lifecycle_operation
from modules.dependency_manager import get_unit_dependencies, dependency_tree
from modules.failure_detector import detect_failed_services, periodic_check
from modules.auto_recovery import RecoveryController
from modules.report_manager import (
    current_status_report, failed_services_report,
    recent_operations_report, recovery_report, historical_report,
)
from utils.validators import validate_service_name, validate_recovery_policy


console = Console()


def print_status(status):
    table = Table(title=f"Status: {status.get('name', '')}")
    table.add_column("Property")
    table.add_column("Value")
    for key, label in (
        ("load", "Load"), ("active", "Runtime state"),
        ("sub", "Sub state"), ("enabled", "Boot enablement"),
        ("description", "Description"),
    ):
        table.add_row(label, str(status.get(key, "unknown")))
    console.print(table)


def ask_service(prompt="Enter service name (for example, ssh.service):"):
    service = Prompt.ask(prompt).strip()
    if not validate_service_name(service):
        console.print("[red]Invalid service name. Use a name ending in .service[/red]")
        return None
    status = get_service_status(service)
    if not status["success"]:
        console.print(f"[red]{status['error']}[/red]")
        return None
    return service


def show_services():
    services = list_services()
    table = Table(title="Systemd Services")
    table.add_column("Service")
    table.add_column("Load")
    table.add_column("Active")
    table.add_column("Sub")
    table.add_column("Description")
    for item in services:
        table.add_row(
            item["name"], item["load"], item["active"],
            item["sub"], item["description"],
        )
    console.print(table)
    console.print(f"Services shown: {len(services)}")


def monitor_status():
    service = ask_service("Enter service to monitor")
    if service:
        print_status(get_service_status(service))


def lifecycle_action(operation):
    service = ask_service(f"Enter service to {operation}")
    if not service:
        return
    if operation in ("stop", "disable", "restart"):
        if not Confirm.ask(f"Confirm {operation} of {service}?", default=False):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
    result = perform_lifecycle_operation(
        service, operation,
        db_path=config.DATABASE_PATH, log_path=config.LOG_FILE_PATH,
    )
    if result["success"]:
        console.print(f"[green]Success: {service} {operation}[/green]")
    else:
        console.print(f"[red]Failed: {result.get('error', 'Unknown error')}[/red]")
    if result.get("after"):
        print_status(result["after"])


def print_dependency_tree(node, prefix="", is_last=True):
    connector = "`-- " if is_last else "|-- "
    relationship = node.get("relationship")
    suffix = ""
    if relationship:
        suffix = f" ({relationship['property']}: {relationship['type']})"
    console.print(prefix + connector + node["name"] + suffix)
    child_prefix = prefix + ("    " if is_last else "|   ")
    children = node.get("children", [])
    for index, child in enumerate(children):
        print_dependency_tree(child, child_prefix, index == len(children) - 1)


def view_dependencies():
    service = ask_service("Enter service")
    if not service:
        return
    relationships = get_unit_dependencies(service)
    if not relationships:
        console.print("[yellow]No dependency metadata returned by systemd.[/yellow]")
    else:
        table = Table(title=f"Dependencies for {service}")
        table.add_column("Property")
        table.add_column("Classification")
        table.add_column("Unit")
        for item in relationships:
            table.add_row(item["property"], item["type"], item["dependency"])
        console.print(table)
    console.print(f"[bold]Tree for {service}[/bold]")
    print_dependency_tree(dependency_tree(service), "", True)


def detect_failures():
    failures = detect_failed_services(db_path=config.DATABASE_PATH)
    if not failures:
        console.print("[green]No failed systemd services detected.[/green]")
        return
    table = Table(title="Failed Services")
    table.add_column("Service")
    table.add_column("Active")
    table.add_column("Sub")
    table.add_column("Evidence")
    for item in failures:
        evidence = item["details"].strip().splitlines()
        table.add_row(
            item["name"], item["active"], item["sub"],
            evidence[-1] if evidence else "journal has no recent entries",
        )
    console.print(table)


def configure_recovery():
    try:
        policy = config.load_monitoring_config()
    except (OSError, ValueError) as exc:
        console.print(f"[red]Unable to load configuration: {exc}[/red]")
        return
    console.print("[bold]Current recovery policy[/bold]")
    console.print(str(policy))
    enabled = Confirm.ask(
        "Enable automatic recovery?",
        default=policy["automatic_recovery_enabled"],
    )
    allowlist_text = Prompt.ask(
        "Recovery allowlist, comma-separated service names",
        default=", ".join(policy["recovery_allowlist"]),
    )
    allowlist = [item.strip() for item in allowlist_text.split(",") if item.strip()]
    for name in allowlist:
        if not validate_service_name(name):
            console.print(f"[red]Invalid service name: {name}[/red]")
            return
    try:
        limit = int(Prompt.ask(
            "Maximum retry attempts",
            default=str(policy["recovery_retry_limit"]),
        ))
        cooldown = float(Prompt.ask(
            "Cooldown in seconds",
            default=str(policy["recovery_cooldown"]),
        ))
    except ValueError:
        console.print("[red]Retry and cooldown values must be numeric.[/red]")
        return
    policy["automatic_recovery_enabled"] = enabled
    policy["recovery_allowlist"] = allowlist
    policy["recovery_retry_limit"] = limit
    policy["recovery_cooldown"] = cooldown
    if not validate_recovery_policy(policy):
        console.print("[red]Invalid recovery policy.[/red]")
        return
    try:
        config.save_monitoring_config(policy)
        console.print("[green]Recovery policy saved.[/green]")
    except (OSError, ValueError) as exc:
        console.print(f"[red]Unable to save policy: {exc}[/red]")


def continuous_monitoring():
    try:
        monitoring_config = config.load_monitoring_config()
    except (OSError, ValueError) as exc:
        console.print(f"[red]Invalid monitoring configuration: {exc}[/red]")
        return
    selected = monitoring_config["services"]
    if not selected:
        value = Prompt.ask("Services to monitor, comma-separated")
        selected = [item.strip() for item in value.split(",") if item.strip()]
    for name in selected:
        if not validate_service_name(name):
            console.print(f"[red]Invalid service name: {name}[/red]")
            return
    interval = monitoring_config["monitoring_interval"]
    recovery = RecoveryController(
        monitoring_config,
        db_path=config.DATABASE_PATH,
        log_path=config.LOG_FILE_PATH,
    )
    console.print(
        f"[bold]Monitoring {', '.join(selected)} every {interval} seconds[/bold]"
    )
    console.print("[yellow]Press Ctrl+C to stop.[/yellow]")
    try:
        while True:
            failures = periodic_check(selected, db_path=config.DATABASE_PATH)
            for failure in failures:
                console.print(
                    f"[red]Failure: {failure['name']} "
                    f"state={failure['status'].get('active')}[/red]"
                )
                recovery_result = recovery.recover(failure["name"])
                if monitoring_config["automatic_recovery_enabled"]:
                    console.print(str(recovery_result))
            if not failures:
                for name in selected:
                    status = get_service_status(name)
                    console.print(
                        f"[green]{name}: {status.get('active', 'unknown')}[/green]"
                    )
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Continuous monitoring stopped.[/yellow]")


def view_activity_logs():
    records = recent_operations_report(db_path=config.DATABASE_PATH)
    table = Table(title="Recent Activity")
    table.add_column("Timestamp")
    table.add_column("Service")
    table.add_column("Operation")
    table.add_column("Result")
    table.add_column("Details")
    for record in records:
        table.add_row(
            record["timestamp"], record["service_name"] or "-",
            record["operation"], record["result"],
            record["error_details"] or "",
        )
    console.print(table)


def generate_reports():
    console.print("[bold]Current status summary[/bold]")
    console.print(str(current_status_report()))
    console.print("[bold]Failed services[/bold]")
    failed = failed_services_report()
    console.print(f"{len(failed)} failed service(s)" if failed else "No failed services")
    console.print("[bold]Recent recovery attempts[/bold]")
    console.print(str(recovery_report(db_path=config.DATABASE_PATH)))
    console.print("[bold]Historical summary[/bold]")
    console.print(str(historical_report(db_path=config.DATABASE_PATH)["counts"]))


MENU = {
    "1": ("View All Services", show_services),
    "2": ("Monitor Service Status", monitor_status),
    "3": ("Start Service", lambda: lifecycle_action("start")),
    "4": ("Stop Service", lambda: lifecycle_action("stop")),
    "5": ("Restart Service", lambda: lifecycle_action("restart")),
    "6": ("Enable Service", lambda: lifecycle_action("enable")),
    "7": ("Disable Service", lambda: lifecycle_action("disable")),
    "8": ("View Service Dependencies", view_dependencies),
    "9": ("Detect Service Failures", detect_failures),
    "10": ("Configure Automatic Recovery", configure_recovery),
    "11": ("Start Continuous Monitoring", continuous_monitoring),
    "12": ("View Activity Logs", view_activity_logs),
    "13": ("Generate Reports", generate_reports),
}


def main():
    try:
        initialize_database(config.DATABASE_PATH)
        if not config.MONITORING_CONFIG_PATH.exists():
            config.save_monitoring_config(config.DEFAULT_MONITORING_CONFIG)
        else:
            config.validate_monitoring_config(config.load_monitoring_config())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]Startup configuration error: {exc}[/red]")
        return 1

    console.print("[bold cyan]Linux Service Dependency and Lifecycle Management System[/bold cyan]")
    while True:
        console.print("\n[bold]Main Menu[/bold]")
        for key, (label, _) in MENU.items():
            console.print(f"{key}. {label}")
        console.print("14. Exit")
        choice = Prompt.ask("Select an option", default="14").strip()
        if choice == "14":
            console.print("[cyan]Goodbye.[/cyan]")
            return 0
        if choice not in MENU:
            console.print("[red]Invalid menu selection.[/red]")
            continue
        try:
            MENU[choice][1]()
        except KeyboardInterrupt:
            console.print("\n[yellow]Returning to the main menu.[/yellow]")
        except Exception as exc:
            console.print(f"[red]Unexpected error: {exc}[/red]")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Application stopped.[/yellow]")
        sys.exit(0)
