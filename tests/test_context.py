from pathlib import Path
from unittest.mock import patch

from ask.context import collect_context
from ask.history import HISTORY_SCAN_LINES


def test_darwin_is_rendered_as_macos(tmp_path: Path) -> None:
    with patch(
        "ask.context.get_context_info",
        return_value={
            "os_name": "macOS",
            "os_version": "15.0",
            "machine": "arm64",
            "hostname": "test-mac",
            "shell": "zsh",
        },
    ):
        ctx = collect_context(tmp_path)

    assert ctx.os_name == "macOS"
    assert "OS: macOS" in ctx.render()


def test_context_includes_project_hints_and_recent_safe_files(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n")
    (tmp_path / "ask").mkdir()
    (tmp_path / "ask" / "cli.py").write_text("print('hi')\n")
    (tmp_path / ".env").write_text("SECRET=value\n")

    ctx = collect_context(tmp_path)
    rendered = ctx.render()

    assert "Python project" in rendered
    assert "local ask CLI source package" in rendered
    assert "ask/cli.py" in rendered
    assert ".env" not in rendered


def test_context_includes_terminal_history_without_secrets(tmp_path: Path) -> None:
    history = tmp_path / ".zsh_history"
    history.write_text(
        ": 1:0;cd ~/Projects/demo\n"
        ": 2:0;export OPENAI_API_KEY=sk-secret\n"
        ": 3:0;rg controller\n"
        ": 4:0;ask 找配置\n"
        ": 5:0;ask\n"
        ": 6:0;\x1b[200~open 乱码�\n"
    )

    with patch.dict("os.environ", {"HISTFILE": str(history)}):
        ctx = collect_context(tmp_path)
    rendered = ctx.render()

    assert "cd ~/Projects/demo" in rendered
    assert "rg controller" in rendered
    assert "OPENAI_API_KEY" not in rendered
    assert "sk-secret" not in rendered
    assert "ask 找配置" not in rendered
    assert "乱码" not in rendered


def test_terminal_history_scans_only_recent_fixed_window(tmp_path: Path) -> None:
    history = tmp_path / ".zsh_history"
    old_lines = [f": {i}:0;old-command-{i}" for i in range(10)]
    filler = [f": {i}:0;recent-command-{i}" for i in range(HISTORY_SCAN_LINES)]
    history.write_text("\n".join(old_lines + filler))

    with patch.dict("os.environ", {"HISTFILE": str(history)}):
        ctx = collect_context(tmp_path)
    rendered = ctx.render()

    assert "old-command-9" not in rendered
    assert "recent-command-199" in rendered
    assert len(ctx.recent_commands) == 12
