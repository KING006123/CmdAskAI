from __future__ import annotations

from ask import ui


def test_strip_fences_streaming_drops_unclosed_opening_fence() -> None:
    # Mid-stream: opening fence arrived, closing fence has not.
    assert ui._strip_fences_streaming("```bash\nls -la") == "ls -la"


def test_strip_fences_streaming_drops_trailing_partial_fence() -> None:
    assert ui._strip_fences_streaming("```bash\nls -la\n``") == "ls -la"


def test_strip_fences_streaming_passthrough_when_no_fence() -> None:
    assert ui._strip_fences_streaming("ls -la") == "ls -la"


def test_command_stream_finalizes_to_terminal_panel(monkeypatch) -> None:
    updates: list[object] = []

    class FakeLive:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def update(self, renderable: object) -> None:
            updates.append(renderable)

    monkeypatch.setattr(ui, "Live", FakeLive)
    safety = ui.SafetyResult(dangerous=False)

    with ui.CommandStream() as stream:
        stream.on_delta("ls ")
        stream.on_delta("-la")
        stream.finalize("ls -la", safety)

    # Last frame is the terminal "Generated command" panel, not "Generating…".
    assert "Generated command" in str(updates[-1].title)
