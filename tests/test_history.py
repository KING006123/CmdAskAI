from pathlib import Path
from unittest.mock import patch

from ask.history import HISTORY_SCAN_LINES
from ask.history import load_recent_commands


def test_load_recent_commands_dedupes_and_filters_secrets(tmp_path: Path) -> None:
    history = tmp_path / ".zsh_history"
    history.write_text(
        ": 1:0;ls\n"
        ": 2:0;export TOKEN=secret\n"
        ": 3:0;rg controller\n"
        ": 4:0;ls\n"
        ": 5:0;echo sk-secret > /tmp/api_key.txt\n"
    )

    with patch.dict("os.environ", {"HISTFILE": str(history)}):
        commands = load_recent_commands("zsh", n=10)

    assert commands == ["rg controller", "ls"]


def test_load_recent_commands_scans_fixed_window(tmp_path: Path) -> None:
    history = tmp_path / ".zsh_history"
    old_lines = [f": {i}:0;old-command-{i}" for i in range(10)]
    recent_lines = [f": {i}:0;recent-command-{i}" for i in range(HISTORY_SCAN_LINES)]
    history.write_text("\n".join(old_lines + recent_lines))

    with patch.dict("os.environ", {"HISTFILE": str(history)}):
        commands = load_recent_commands("zsh", n=12)

    assert "old-command-9" not in commands
    assert commands[-1] == "recent-command-199"
    assert len(commands) == 12
