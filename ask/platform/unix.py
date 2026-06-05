from __future__ import annotations

import os
import platform as py_platform
import subprocess
from pathlib import Path


def get_shell() -> str:
    return Path(os.environ.get("SHELL", "/bin/sh")).name


def get_context_info() -> dict[str, str]:
    system = py_platform.system()
    os_name = "macOS" if system == "Darwin" else system
    return {
        "os_name": os_name,
        "os_version": py_platform.mac_ver()[0] or py_platform.release(),
        "machine": py_platform.machine(),
        "shell": get_shell(),
        "hostname": py_platform.node(),
    }


def run_shell_command(command: str) -> subprocess.CompletedProcess[str]:
    shell = os.environ.get("SHELL") or "/bin/sh"
    return subprocess.run(
        command,
        shell=True,
        executable=shell,
        capture_output=True,
        text=True,
        check=False,
    )


def get_history_file() -> Path | None:
    histfile = os.environ.get("HISTFILE", "").strip()
    if histfile:
        path = Path(histfile).expanduser()
        return path if path.exists() else None

    candidates = {
        "zsh": Path.home() / ".zsh_history",
        "bash": Path.home() / ".bash_history",
        "fish": Path.home() / ".local/share/fish/fish_history",
    }
    path = candidates.get(get_shell())
    return path if path and path.exists() else None


def get_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "ask"
