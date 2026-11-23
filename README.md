# Linux Service Dependency and Lifecycle Management System

## Description

This application is a command-line Linux system administration tool that discovers and manages real systemd service units. It uses `systemctl` and `journalctl`, stores operation history in SQLite, and provides failure detection, dependency analysis, reporting, and optional controlled automatic recovery.

## Features

- Discover and inspect systemd services
- Monitor runtime and boot-enablement states
- Start, stop, restart, enable, disable, and reload services
- Inspect Requires, Wants, Requisite, BindsTo, PartOf, After, and Before relationships
- Display bounded dependency trees
- Detect failed services and unhealthy requirement dependencies
- Read recent journal evidence
- Store activity, failures, and recovery attempts
- Periodically monitor configured services
- Use an explicit, disabled-by-default recovery allowlist
- Generate terminal reports

## Technologies

- Python 3
- systemd, `systemctl`, and `journalctl`
- SQLite through the Python standard library
- Rich for terminal tables and prompts
- pytest for unit tests

## Project Structure

```text
linux-service-manager/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
├── modules/
├── utils/
├── database/
├── config/monitoring.json
├── logs/activity.log
├── data/service_manager.db
└── tests/
```

Runtime database and log files are created automatically and are excluded from Git.

## Major Modules

- `main.py`: CLI entry point and menu.
- `config.py`: centralized paths and default settings.
- `modules/service_monitor.py`: real systemd service discovery and status.
- `modules/lifecycle_manager.py`: lifecycle operations and post-operation verification.
- `modules/dependency_manager.py`: unit relationships and bounded dependency trees.
- `modules/failure_detector.py`: failed-unit checks and journal evidence.
- `modules/auto_recovery.py`: allowlisted, cooldown-limited recovery.
- `modules/log_manager.py`: human-readable and SQLite activity logging.
- `modules/report_manager.py`: current and historical reports.
- `utils/command_executor.py`: safe `subprocess.run()` wrapper.
- `utils/validators.py`: service, operation, and policy validation.
- `database/connection.py`: SQLite initialization.
- `database/operations.py`: parameterized history operations.

## Prerequisites

- Ubuntu or another Linux distribution running systemd
- Python 3.10 or newer
- `systemctl`
- `journalctl`
- Permission to execute only the service operations that require administrator privileges

Read-only discovery and status checks normally do not require root. Start, stop, restart, enable, and disable operations can require administrator privileges.

## Installation

Clone the repository and enter it:

```bash
git clone <repository-url>
cd linux-service-manager
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Run

```bash
python3 main.py
```

The menu offers service discovery, status monitoring, lifecycle operations, dependency trees, failure detection, recovery configuration, continuous monitoring, logs, and reports.

## Permissions

If a lifecycle command is denied, do not run the entire application as root. Run only the required operation with administrative privileges:

```bash
sudo systemctl start test.service
sudo systemctl stop test.service
sudo systemctl restart test.service
sudo systemctl enable test.service
sudo systemctl disable test.service
```

The application itself remains a normal user process and reports permission failures instead of bypassing systemd authorization.

## Automatic Recovery

Automatic recovery is disabled by default. Open menu option 10 and explicitly configure:

- `automatic_recovery_enabled`
- an allowlist of exact `.service` unit names
- maximum recovery attempts
- cooldown seconds

The recovery controller refuses critical system services, services outside the allowlist, services that are not failed, services with unhealthy requirement dependencies, retry-limit exhaustion, and cooldown violations.

The recovery policy is stored in `config/monitoring.json`. It is safe to edit it by hand, but it is validated before use.

## Database and Logs

The SQLite database is created at `data/service_manager.db`.

Tables:

- `service_activity`: lifecycle and monitoring operations
- `service_failures`: failed units and dependency failures
- `recovery_history`: recovery attempts and outcomes

Human-readable logs are written to `logs/activity.log`. No service status or command result is simulated.

## Testing

Run all tests:

```bash
source .venv/bin/activate
pytest -q
```

Run compilation checks:

```bash
python3 -m compileall -q main.py config.py modules utils database tests
```

Unit tests mock systemd commands where appropriate. Read-only real-system integration checks can be run manually:

```bash
python3 - <<'PY'
from modules.service_monitor import list_services, get_service_status
print(len(list_services()))
print(get_service_status("dbus.service"))
PY
```

## Test Status

The unit suite currently passes 14 tests. Real discovery also found 178 known service units in the development environment, and a real `dbus.service` status/dependency inspection succeeded.

Privileged start, stop, restart, enable, and disable experiments against disposable test services remain environment-dependent. Do not test against essential Ubuntu services.

## Troubleshooting

- `systemctl: command not found`: the host is not a systemd environment or systemctl is missing.
- `Permission denied`: use only the required sudo command and retry.
- `Unit not found`: verify the exact unit name with option 1.
- Invalid `.service` name: use a unit name ending in `.service`.
- No dependencies displayed: the unit may not be loaded or systemd may expose no relationship properties.
- CLI cannot start: reinstall requirements with `python3 -m pip install -r requirements.txt`.
