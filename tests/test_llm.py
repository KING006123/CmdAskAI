from types import SimpleNamespace

from ask.llm import _collect_stream
from ask.llm import _stream_delta_content
from ask.llm import parse_candidate_commands
from ask.llm import strip_fences


def test_strip_fences_removes_bash_fence() -> None:
    assert strip_fences("```bash\nls -la\n```") == "ls -la"


def test_strip_fences_keeps_multiline_command() -> None:
    text = "find . -name '*.py' \\\n  -mtime -2"
    assert strip_fences(text) == text


def test_parse_candidate_commands_limits_and_filters_empty_lines() -> None:
    text = "```bash\nls -la\n\nfind . -maxdepth 1 -type f\ndu -sh *\n```"

    assert parse_candidate_commands(text, 2) == ["ls -la", "find . -maxdepth 1 -type f"]


def test_stream_delta_content_reads_openai_chunk_shape() -> None:
    chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ls"))])

    assert _stream_delta_content(chunk) == "ls"


def test_collect_stream_joins_deltas_and_calls_callback() -> None:
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ls"))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=" -la"))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
    ]
    seen: list[str] = []

    result = _collect_stream(chunks, seen.append)

    assert result == "ls -la"
    assert seen == ["ls", " -la"]
