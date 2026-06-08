from __future__ import annotations

import re
from contextlib import contextmanager
from collections.abc import Iterator

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

from ask.safety import SafetyResult


console = Console(stderr=True)


def _command_panel(command: str, title: str, border: str) -> Panel:
    syntax = Syntax(command or " ", "bash", theme="ansi_dark", word_wrap=True)
    return Panel(syntax, title=title, border_style=border)


def _print_safety_warnings(safety: SafetyResult) -> None:
    if not safety.dangerous:
        return
    console.print("[bold red]Potentially dangerous command[/bold red]")
    for reason in safety.reasons:
        console.print(f"[red]- {reason}[/red]")
    if safety.dry_run_hint:
        console.print(f"[yellow]Suggested dry-run:[/yellow] {safety.dry_run_hint}")


def show_command(command: str, safety: SafetyResult) -> None:
    border = "red" if safety.dangerous else "green"
    console.print(_command_panel(command, "Generated command", border))
    _print_safety_warnings(safety)


class CommandStream:
    """Render a streamed command inside a single Live panel.

    The panel grows in place while tokens arrive and, on ``finalize``, turns
    into the final command panel (green/red border) so the stream ends on the
    terminal state with no second redraw.
    """

    def __init__(self, title: str = "Generating command") -> None:
        self._title = title
        self._buffer = ""
        self._safety: SafetyResult | None = None
        self._live = Live(console=console, refresh_per_second=12, transient=False)

    def __enter__(self) -> CommandStream:
        self._live.start()
        self._update_generating()
        return self

    def on_delta(self, delta: str) -> None:
        self._buffer += delta
        self._update_generating()

    def finalize(self, command: str, safety: SafetyResult) -> None:
        self._safety = safety
        border = "red" if safety.dangerous else "green"
        self._live.update(_command_panel(command, "Generated command", border))

    def __exit__(self, *exc: object) -> None:
        self._live.stop()
        if self._safety is not None:
            _print_safety_warnings(self._safety)

    def _update_generating(self) -> None:
        body = _strip_fences_streaming(self._buffer)
        self._live.update(_command_panel(body, f"{self._title}…", "cyan"))


@contextmanager
def thinking(message: str = "asking…") -> Iterator[None]:
    """Single-line spinner on stderr for widget/raw mode (clears on exit)."""
    with console.status(f"[cyan]{message}", spinner="dots"):
        yield


def _strip_fences_streaming(text: str) -> str:
    """Best-effort fence removal for partial streamed text.

    Unlike ``strip_fences`` it must cope with an opening fence whose closing
    fence has not arrived yet, so the panel never flashes raw ``` markers.
    """
    cleaned = text.lstrip()
    if cleaned.startswith("```"):
        newline = cleaned.find("\n")
        cleaned = cleaned[newline + 1:] if newline != -1 else ""
    cleaned = re.sub(r"\n?`{1,3}\s*$", "", cleaned)
    return cleaned


def choose_candidate(commands: list[str]) -> str | None:
    if not commands:
        return None

    for index, command in enumerate(commands, start=1):
        syntax = Syntax(command, "bash", theme="ansi_dark", word_wrap=True)
        console.print(Panel(syntax, title=f"Candidate {index}", border_style="cyan"))

    choices = [str(index) for index in range(1, len(commands) + 1)] + ["q"]
    answer = Prompt.ask("Choose candidate", choices=choices, default="q")
    if answer == "q":
        return None
    return commands[int(answer) - 1]


def choose_action(dangerous: bool = False) -> str:
    if dangerous:
        console.print("[bold]Actions[/bold]: [r]un  [d]ry-run  [e]dit  [c]opy  e[x]plain  [q]uit")
        return Prompt.ask("Choose", choices=["r", "d", "e", "c", "x", "q"], default="q")
    console.print("[bold]Actions[/bold]: [r]un  [e]dit  [c]opy  e[x]plain  [q]uit")
    return Prompt.ask("Choose", choices=["r", "e", "c", "x", "q"], default="q")


def confirm_run(dangerous: bool) -> bool:
    if not Confirm.ask("Run this command?", default=False):
        return False
    if dangerous:
        return Confirm.ask("Danger warning acknowledged. Run anyway?", default=False)
    return True


def show_explanation(explanation: str) -> None:
    console.print(Panel(explanation, title="Explanation", border_style="blue"))


def show_dry_run_hint(hint: str) -> None:
    console.print(Panel(hint, title="Suggested dry-run", border_style="yellow"))


def ask_continue() -> str | None:
    answer = Prompt.ask("Continue? Enter next task or press Enter to quit", default="")
    return answer.strip() or None


def show_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")
