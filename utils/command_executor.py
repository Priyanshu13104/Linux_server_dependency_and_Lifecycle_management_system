import shutil
import subprocess

from config import COMMAND_TIMEOUT


def execute(command, timeout=COMMAND_TIMEOUT):
    if not isinstance(command, (list, tuple)) or not command:
        return {"success": False, "stdout": "", "stderr": "Invalid command.", "returncode": None}
    if shutil.which(command[0]) is None:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command not found: {command[0]}",
            "returncode": None,
        }
    try:
        completed = subprocess.run(
            list(command),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": completed.returncode == 0,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out.", "returncode": None}
    except PermissionError:
        return {"success": False, "stdout": "", "stderr": "Permission denied.", "returncode": None}
    except OSError as exc:
        return {"success": False, "stdout": "", "stderr": str(exc), "returncode": None}
