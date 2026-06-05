from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

import pyperclip
from ask.platform import run_shell_command
from prompt_toolkit import prompt
from rich.console import Console


OUTPUT_LIMIT = 2000
console = Console()


@dataclass(frozen=True)
class RunResult:
    returncode: int
    output: str


def edit_command(command: str) -> str:
    return prompt("edit> ", default=command).strip()


def copy_command(command: str) -> None:
    pyperclip.copy(command)


def run_command(command: str) -> RunResult:
    try:
        proc = run_shell_command(command)
    except (OSError, subprocess.SubprocessError) as exc:
        message = str(exc)
        console.print(message)
        return RunResult(returncode=1, output=_truncate_output(message))

    combined = (proc.stdout or "") + (proc.stderr or "")
    if combined:
        console.print(combined, end="")
    return RunResult(returncode=proc.returncode, output=_truncate_output(combined))


def _truncate_output(output: str, limit: int = OUTPUT_LIMIT) -> str:
    if len(output) <= limit:
        return output
    return output[-limit:]
