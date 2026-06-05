from __future__ import annotations

import re
from dataclasses import dataclass


DANGEROUS_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\s+/(?:\s|$)", "force-removes the filesystem root"),
    (r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\s+\*", "force-removes many files"),
    (r"\bdd\s+", "uses dd, which can overwrite disks"),
    (r"\bmkfs(?:\.[A-Za-z0-9]+)?\b", "formats a filesystem"),
    (r">\s*/dev/(?:disk|rdisk|sda|nvme)", "writes directly to a device"),
    (r":\(\)\{\s*:\|:&\s*\};:", "contains a fork bomb pattern"),
    (r"\bchmod\s+-R\s+777\b", "recursively makes files world-writable"),
    (r"\bsudo\s+rm\b", "removes files with elevated privileges"),
    (r"\bshutdown\b|\breboot\b", "powers off or restarts the machine"),
)

DRY_RUN_HINTS: tuple[tuple[str, str], ...] = (
    (r"\brm\b", "ls -la <targets>  # preview what would be deleted"),
    (r"\bdd\b", "diskutil list  # verify block devices before dd on macOS"),
    (r"\bmkfs\b", "diskutil list  # check target device first on macOS"),
    (r"\bchmod\s+-R\b", "ls -la <target>  # check current permissions"),
)


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
