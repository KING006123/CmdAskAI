from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

from ask.safety import SafetyResult


console = Console(stderr=True)


def show_command(command: str, safety: SafetyResult) -> None:
    syntax = Syntax(command, "bash", theme="ansi_dark", word_wrap=True)
    border = "red" if safety.dangerous else "green"
    title = "Generated command"
    console.print(Panel(syntax, title=title, border_style=border))
    if safety.dangerous:
        console.print("[bold red]Potentially dangerous command[/bold red]")
        for reason in safety.reasons:
            console.print(f"[red]- {reason}[/red]")
        if safety.dry_run_hint:
            console.print(f"[yellow]Suggested dry-run:[/yellow] {safety.dry_run_hint}")


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
