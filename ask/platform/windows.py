from __future__ import annotations

import os
import platform as py_platform
import subprocess
from pathlib import Path


def get_shell() -> str:
    if os.environ.get("PSModulePath"):
        return "powershell"
    return "cmd"


def get_context_info() -> dict[str, str]:
    return {
        "os_name": "Windows",
        "os_version": py_platform.version(),
        "machine": py_platform.machine(),
        "shell": get_shell(),
        "hostname": py_platform.node(),
    }


def run_shell_command(command: str) -> subprocess.CompletedProcess[str]:
    if get_shell() == "powershell":
        args = ["powershell", "-NoProfile", "-Command", command]
    else:
        args = ["cmd", "/c", command]
    return subprocess.run(args, capture_output=True, text=True, check=False)


def get_history_file() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    path = (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "PowerShell"
        / "PSReadLine"
        / "ConsoleHost_history.txt"
    )
    return path if path.exists() else None


def get_config_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home())
    return Path(appdata) / "ask"
