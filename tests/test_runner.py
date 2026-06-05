from ask.runner import _truncate_output
from ask.runner import run_command


def test_truncate_output_keeps_tail() -> None:
    output = "a" * 2100

    truncated = _truncate_output(output, limit=2000)

    assert len(truncated) == 2000
    assert truncated == "a" * 2000


def test_run_command_captures_output() -> None:
    result = run_command("printf hello")

    assert result.returncode == 0
    assert result.output == "hello"

