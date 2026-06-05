from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ask.config import AskConfig
from ask.history import load_recent_commands
from ask.platform import get_context_info
from ask.platform import get_shell

RECENT_COMMAND_LIMIT = 12


@dataclass(frozen=True)
class ShellContext:
    os_name: str
    os_release: str
    machine: str
    hostname: str
    shell: str
    cwd: str
    terminal_tools: tuple[str, ...]
    shell_aliases: tuple[str, ...]
    recent_commands: tuple[str, ...]
    git_branch: str | None
    git_status: tuple[str, ...]
    project_hints: tuple[str, ...]
    entries: tuple[str, ...]
    recent_files: tuple[str, ...]

    def render(self) -> str:
        branch = self.git_branch or "not a git repository"
        git_status = "\n".join(f"- {item}" for item in self.git_status) or "- no git status available"
        project_hints = "\n".join(f"- {item}" for item in self.project_hints) or "- unknown"
        entries = "\n".join(f"- {entry}" for entry in self.entries) or "- empty directory"
        recent_files = "\n".join(f"- {entry}" for entry in self.recent_files) or "- no recent files found"
        terminal_tools = ", ".join(self.terminal_tools) or "unknown"
        shell_aliases = "\n".join(f"- {item}" for item in self.shell_aliases) or "- no safe aliases found"
        recent_commands = "\n".join(f"- {item}" for item in self.recent_commands) or "- no safe recent commands found"
        return (
            f"OS: {self.os_name} {self.os_release} ({self.machine})\n"
            f"Hostname: {self.hostname}\n"
            f"Shell: {self.shell}\n"
            f"Current directory: {self.cwd}\n"
            f"Available terminal tools: {terminal_tools}\n"
            f"Safe shell aliases:\n{shell_aliases}\n"
            f"Safe recent terminal commands:\n{recent_commands}\n"
            f"Git branch: {branch}\n"
            f"Git status:\n{git_status}\n"
            f"Project hints:\n{project_hints}\n"
            f"Directory entries:\n{entries}\n"
            f"Recently modified safe files:\n{recent_files}"
        )


def collect_context(cwd: Path | None = None, cfg: AskConfig | None = None) -> ShellContext:
    current = (cwd or Path.cwd()).resolve()
    platform_info = get_context_info()
    shell = platform_info.get("shell") or get_shell()
    history_lines = cfg.history_lines if cfg is not None else RECENT_COMMAND_LIMIT
    return ShellContext(
        os_name=platform_info.get("os_name", "unknown"),
        os_release=platform_info.get("os_version", "unknown"),
        machine=platform_info.get("machine", ""),
        hostname=platform_info.get("hostname", ""),
        shell=shell,
        cwd=str(current),
        terminal_tools=tuple(_available_tools()),
        shell_aliases=tuple(_shell_aliases()),
        recent_commands=tuple(load_recent_commands(shell, history_lines)),
        git_branch=_git_branch(current),
        git_status=tuple(_git_status(current)),
        project_hints=tuple(_project_hints(current)),
        entries=tuple(_directory_summary(current)),
        recent_files=tuple(_recent_files(current)),
    )


def _available_tools() -> list[str]:
    candidates = [
        "rg",
        "fd",
        "find",
        "grep",
        "sed",
        "awk",
        "git",
        "python3",
        "node",
        "npm",
        "pnpm",
        "mvn",
        "java",
        "docker",
        "brew",
        "curl",
        "jq",
        "fzf",
        "zoxide",
    ]
    return [tool for tool in candidates if shutil.which(tool)]


def _shell_aliases(limit: int = 30) -> list[str]:
    zshrc = Path.home() / ".zshrc"
    if not zshrc.exists():
        return []

    aliases: list[str] = []
    try:
        lines = zshrc.read_text(errors="replace").splitlines()
    except OSError:
        return []

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("alias ") or _contains_sensitive_text(stripped):
            continue
        aliases.append(stripped.removeprefix("alias "))
        if len(aliases) >= limit:
            break
    return aliases


def _git_branch(cwd: Path) -> str | None:
    if shutil.which("git") is None:
        return None
    try:
        proc = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=1.5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    branch = proc.stdout.strip()
    return branch or None


def _git_status(cwd: Path, limit: int = 30) -> list[str]:
    if shutil.which("git") is None:
        return []
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=1.5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return lines[:limit]


def _project_hints(cwd: Path) -> list[str]:
    markers = {
        "pyproject.toml": "Python project",
        "requirements.txt": "Python dependencies",
        "package.json": "Node.js project",
        "pom.xml": "Maven/Spring Boot project",
        "build.gradle": "Gradle project",
        "docker-compose.yml": "Docker Compose setup",
        "Dockerfile": "Docker image setup",
        ".git": "Git repository",
        "README.md": "README present",
    }
    hints = [label for name, label in markers.items() if (cwd / name).exists()]

    if (cwd / "ask").is_dir():
        hints.append("local ask CLI source package")
    if (cwd / "tests").is_dir():
        hints.append("test suite present")
    return hints


def _directory_summary(cwd: Path, limit: int = 40) -> list[str]:
    entries: list[str] = []
    ignored_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}
    try:
        children = sorted(cwd.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return entries

    for child in children[:limit]:
        if child.is_dir() and child.name in ignored_dirs:
            continue
        if _looks_sensitive(child):
            continue
        marker = "/" if child.is_dir() else ""
        entries.append(f"{child.name}{marker}")
    if len(children) > limit:
        entries.append(f"... {len(children) - limit} more")
    return entries


def _recent_files(cwd: Path, limit: int = 25) -> list[str]:
    candidates: list[Path] = []
    ignored_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}
    ignored_suffixes = {".pyc", ".pyo", ".so", ".dylib", ".dll"}
    scanned = 0

    try:
        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            root_path = Path(root)
            for name in files:
                scanned += 1
                if scanned > 2000:
                    dirs.clear()  # stop os.walk from descending further
                    break
                path = root_path / name
                if path.suffix in ignored_suffixes or _looks_sensitive(path):
                    continue
                candidates.append(path)
    except OSError:
        return []

    candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return [_safe_relative_path(path, cwd) for path in candidates[:limit]]


def _has_ignored_part(path: Path, ignored_dirs: set[str]) -> bool:
    return any(part in ignored_dirs for part in path.parts)


def _looks_sensitive(path: Path) -> bool:
    name = path.name.lower()
    sensitive_names = {".env", ".env.local", ".npmrc", ".pypirc", "id_rsa", "id_ed25519"}
    sensitive_words = ("secret", "token", "password", "credential", "private_key")
    return name in sensitive_names or any(word in name for word in sensitive_words)


def _contains_sensitive_text(text: str) -> bool:
    lowered = text.lower()
    sensitive_words = (
        "api_key",
        "apikey",
        "authorization",
        "bearer ",
        "cookie",
        "credential",
        "passwd",
        "password",
        "private_key",
        "secret",
        "sk-",
        "token",
        "key=",
        "api_key",
        "apikey",
    )
    return any(word in lowered for word in sensitive_words)


def _safe_relative_path(path: Path, cwd: Path) -> str:
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)
