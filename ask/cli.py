from __future__ import annotations

import argparse
import sys

from ask import __version__
from ask.config import AskConfig
from ask.config import ConfigError, load_config
from ask.context import collect_context
from ask.llm import (
    LlmError,
    explain_command,
    gen_command,
    gen_command_stream,
    gen_commands,
    gen_next_step_stream,
)
from ask.runner import RunResult
from ask.runner import copy_command, edit_command, run_command
from ask.safety import inspect_command
from ask.ui import (
    CommandStream,
    ask_continue,
    choose_action,
    choose_candidate,
    confirm_run,
    show_command,
    show_dry_run_hint,
    show_error,
    show_explanation,
    thinking,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ask", description="Turn natural language into shell commands.")
    parser.add_argument("request", nargs="*", help="Natural language command request.")
    parser.add_argument("--raw", action="store_true", help="Print only the generated command.")
    parser.add_argument("--stream", action="store_true", help="With --raw, show a spinner on stderr while generating (e.g. the Ctrl+G widget).")
    parser.add_argument("--candidates", type=int, default=None, metavar="N", help="Generate N command candidates.")
    parser.add_argument("--debug-context", action="store_true", help="Print the safe local context sent to the model.")
    parser.add_argument("--export-config", action="store_true", help="Print a redacted shareable config.")
    parser.add_argument("-e", "--explain", action="store_true", help="Explain the generated command.")
    parser.add_argument("--version", action="version", version=f"ask {__version__}")
    args = parser.parse_args(argv)

    if args.debug_context:
        print(collect_context().render())
        return 0

    if args.export_config:
        try:
            cfg = load_config(require_api_key=False)
        except ConfigError as exc:
            show_error(str(exc))
            return 1
        print(_export_config(cfg))
        return 0

    natural_language = " ".join(args.request).strip()
    if not natural_language:
        parser.print_help(sys.stderr)
        return 2

    try:
        cfg = load_config()
        ctx = collect_context(cfg=cfg).render()
        candidate_count = args.candidates if args.candidates is not None else cfg.candidates
        if candidate_count < 1:
            raise ConfigError("candidates must be 1 or greater.")

        # Raw mode (e.g. the Ctrl+G shell widget) wants only the command on
        # stdout. Never stream tokens to the terminal here: the line editor
        # owns the screen. A lightweight spinner is the only feedback.
        if args.raw:
            if candidate_count > 1:
                commands = gen_commands(natural_language, ctx, cfg, n=candidate_count)
                print("\n".join(commands))
                return 0
            command = _generate_raw(natural_language, ctx, cfg, spinner=args.stream)
            print(command)
            return 0

        rendered = False
        if candidate_count > 1:
            commands = gen_commands(natural_language, ctx, cfg, n=candidate_count)
            command = choose_candidate(commands)
            if command is None:
                return 0
        else:
            command = _stream_command(natural_language, ctx, cfg)
            rendered = True
    except (ConfigError, LlmError) as exc:
        if args.raw:
            print(f"ask: {exc}", file=sys.stderr)
        else:
            show_error(str(exc))
        return 1

    if args.explain:
        return _explain(command, cfg)

    return _command_loop(command, natural_language, ctx, cfg, rendered=rendered)


def _command_loop(command: str, original_nl: str, ctx: str, cfg: AskConfig, rendered: bool = False) -> int:
    current_command = command
    if not rendered:
        show_command(current_command, inspect_command(current_command))
    while True:
        safety = inspect_command(current_command)
        action = choose_action(safety.dangerous)
        if action == "q":
            return 0
        if action == "c":
            copy_command(current_command)
            return 0
        if action == "x":
            _explain(current_command, cfg)
            continue
        if action == "d":
            if safety.dry_run_hint:
                show_dry_run_hint(safety.dry_run_hint)
            else:
                show_error("No dry-run hint is defined for this command.")
            continue
        if action == "e":
            current_command = edit_command(current_command)
            if not current_command:
                return 0
            safety = inspect_command(current_command)
            show_command(current_command, safety)
            continue
        if action == "r":
            if confirm_run(safety.dangerous):
                result = run_command(current_command)
                follow_up = ask_continue()
                if follow_up is None:
                    return result.returncode
                next_command = _next_step(original_nl, current_command, result, follow_up, ctx, cfg)
                if next_command is None:
                    return 1
                current_command = next_command
                continue
            return 0


def _next_step(
    original_nl: str,
    command: str,
    result: RunResult,
    follow_up: str,
    ctx: str,
    cfg: AskConfig,
) -> str | None:
    try:
        return _stream_next_step(f"{original_nl}\nFollow-up: {follow_up}", command, result.output, ctx, cfg)
    except LlmError as exc:
        show_error(str(exc))
        return None


def _explain(command: str, cfg: AskConfig) -> int:
    try:
        explanation = explain_command(command, cfg)
    except LlmError as exc:
        show_error(str(exc))
        return 1
    show_explanation(explanation)
    return 0


def _generate_raw(natural_language: str, ctx: str, cfg: AskConfig, spinner: bool) -> str:
    if not spinner:
        return gen_command(natural_language, ctx, cfg)
    with thinking():
        return gen_command(natural_language, ctx, cfg)


def _stream_command(natural_language: str, ctx: str, cfg: AskConfig) -> str:
    with CommandStream() as stream:
        command = gen_command_stream(natural_language, ctx, cfg, on_delta=stream.on_delta)
        stream.finalize(command, inspect_command(command))
    return command


def _stream_next_step(original_nl: str, command: str, result: str, ctx: str, cfg: AskConfig) -> str:
    with CommandStream(title="Next command") as stream:
        next_command = gen_next_step_stream(
            original_nl, command, result, ctx, cfg, on_delta=stream.on_delta
        )
        stream.finalize(next_command, inspect_command(next_command))
    return next_command


def _export_config(cfg: AskConfig) -> str:
    return "\n".join(
        [
            "# ask config - generated by 'ask --export-config'",
            "[provider]",
            f'name = "{cfg.provider}"',
            f'base_url = "{cfg.base_url}"',
            f'api_key = "YOUR_API_KEY_HERE"',
            f'model = "{cfg.model}"',
            "",
            "[ui]",
            f'default_action = "{cfg.default_action}"',
            f"history_lines = {cfg.history_lines}",
            f"candidates = {cfg.candidates}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
