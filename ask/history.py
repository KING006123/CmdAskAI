from __future__ import annotations

import os
import re
from pathlib import Path

from ask.platform import get_history_file
from ask.platform import get_shell

HISTORY_TAIL_BYTES = 64 * 1024
HISTORY_SCAN_LINES = 200


def load_recent_commands(shell: str | None = None, n: int = 20) -> list[str]:
    if n <= 0:
        return []

    shell_name = shell or get_shell()
    history_file = get_history_file()
    if history_file is None or not history_file.exists():
        return []

    try:
        lines = _tail_lines(history_file, max_bytes=HISTORY_TAIL_BYTES, max_lines=HISTORY_SCAN_LINES)
    except OSError:
        return []

    commands: list[str] = []
    seen: set[str] = set()
    for raw in reversed(lines):
        command = _parse_history_command(raw, shell_name)
        if not command or _skip_history_command(command) or command in seen:
            continue
        commands.append(command)
        seen.add(command)
        if len(commands) >= n:
            break
    return list(reversed(commands))


def _tail_lines(path: Path, max_bytes: int, max_lines: int) -> list[str]:
    size = path.stat().st_size
    with path.open("rb") as fh:
        if size > max_bytes:
            fh.seek(size - max_bytes)
            fh.readline()
        data = fh.read(max_bytes)

    text = data.decode(errors="replace")
    return text.splitlines()[-max_lines:]


def _parse_history_command(raw: str, shell: str) -> str:
    line = raw.strip()
    if not line:
        return ""
    if shell == "zsh":
        match = re.match(r"^: \d+:\d+;(.*)$", line)
        if match:
            return _sanitize_history_command(match.group(1))
    return _sanitize_history_command(line)


def _sanitize_history_command(command: str) -> str:
    without_ansi = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", command)
    without_controls = "".join(
        char for char in without_ansi if char == "\t" or char == "\n" or ord(char) >= 32
    )
    return re.sub(r"\s+", " ", without_controls).strip()


def _skip_history_command(command: str) -> bool:
    lowered = command.lower()
    if "�" in command:
        return True
    if re.search(r"(export|password|token|secret|key|api|apikey|api_key|authorization|bearer|cookie|sk-)|=", lowered):
        return True
    noisy_exact = {"ask", "history", "clear", "exit"}
    noisy_prefixes = ("ask ", "ask-key", "source ~/.zshrc")
    return lowered in noisy_exact or lowered.startswith(noisy_prefixes)
