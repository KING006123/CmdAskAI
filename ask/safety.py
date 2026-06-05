from __future__ import annotations

import re
import sys
from dataclasses import dataclass


DANGEROUS_PATTERNS: tuple[tuple[str, str], ...] = (
    # Unix / cross-platform
    (r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\s+/(?:\s|$)", "force-removes the filesystem root"),
    (r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\s+\*", "force-removes many files"),
    (r"\bdd\s+", "uses dd, which can overwrite disks"),
    (r"\bmkfs(?:\.[A-Za-z0-9]+)?\b", "formats a filesystem"),
    (r">\s*/dev/(?:disk|rdisk|sda|nvme)", "writes directly to a device"),
    (r":\(\)\{\s*:\|:&\s*\};:", "contains a fork bomb pattern"),
    (r"\bchmod\s+-R\s+777\b", "recursively makes files world-writable"),
    (r"\bsudo\s+rm\b", "removes files with elevated privileges"),
    (r"\bshutdown\b|\breboot\b", "powers off or restarts the machine"),
    # Windows-specific
    (r"\bRemove-Item\b.{0,60}-Recurse\b.{0,60}-Force\b", "recursively force-deletes files (PowerShell)"),
    (r"\brd\s+/s\b", "recursively deletes a directory tree (cmd)"),
    (r"\bdel\s+/[fsq]*f[fsq]*\b", "force-deletes files (cmd)"),
    (r"\bformat\s+[a-zA-Z]:", "formats a Windows drive"),
    (r"\bFormat-Volume\b", "formats a Windows volume (PowerShell)"),
)

_DRY_RUN_HINTS_UNIX: tuple[tuple[str, str], ...] = (
    (r"\brm\b", "ls -la <targets>  # preview what would be deleted"),
    (r"\bdd\b", "diskutil list  # verify block devices before dd"),
    (r"\bmkfs\b", "diskutil list  # check target device first"),
    (r"\bchmod\s+-R\b", "ls -la <target>  # check current permissions"),
)

_DRY_RUN_HINTS_WINDOWS: tuple[tuple[str, str], ...] = (
    (r"\bRemove-Item\b", "Get-ChildItem <target> -Recurse  # preview what would be deleted"),
    (r"\brd\b|\bdel\b", "dir <target>  # preview what would be deleted"),
    (r"\bformat\b|\bFormat-Volume\b", "Get-Disk  # verify target disk before formatting"),
    (r"\bchmod\b", "Get-Acl <target>  # check current permissions"),
)

DRY_RUN_HINTS = _DRY_RUN_HINTS_WINDOWS if sys.platform == "win32" else _DRY_RUN_HINTS_UNIX


@dataclass(frozen=True)
class SafetyResult:
    dangerous: bool
    reasons: tuple[str, ...] = ()
    dry_run_hint: str | None = None


def inspect_command(command: str) -> SafetyResult:
    reasons = [
        reason
        for pattern, reason in DANGEROUS_PATTERNS
        if re.search(pattern, command, flags=re.IGNORECASE | re.MULTILINE)
    ]

    if "# DANGER" in command.upper():
        reasons.append("the model explicitly marked this command as dangerous")

    dry_run_hint = _dry_run_hint(command) if reasons else None
    return SafetyResult(
        dangerous=bool(reasons),
        reasons=tuple(dict.fromkeys(reasons)),
        dry_run_hint=dry_run_hint,
    )


def _dry_run_hint(command: str) -> str | None:
    for pattern, hint in DRY_RUN_HINTS:
        if re.search(pattern, command, flags=re.IGNORECASE | re.MULTILINE):
            return hint
    return None
