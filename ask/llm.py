from __future__ import annotations

import re

from openai import OpenAI
from openai import OpenAIError

from ask.config import AskConfig
from ask.prompt import build_explain_prompt, build_system_prompt


class LlmError(RuntimeError):
    """Raised when the configured LLM provider cannot return a usable answer."""


def gen_command(natural_language: str, ctx: str, cfg: AskConfig) -> str:
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    try:
        resp = client.chat.completions.create(
            model=cfg.model,
            max_tokens=300,
            temperature=0.1,
            messages=[
                {"role": "system", "content": build_system_prompt(ctx)},
                {"role": "user", "content": natural_language},
            ],
        )
    except OpenAIError as exc:
        raise LlmError(f"LLM request failed: {exc}") from exc

    content = resp.choices[0].message.content or ""
    command = strip_fences(content)
    if not command:
        raise LlmError("LLM returned an empty command.")
    return command


def gen_commands(natural_language: str, ctx: str, cfg: AskConfig, n: int = 3) -> list[str]:
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    try:
        resp = client.chat.completions.create(
            model=cfg.model,
            max_tokens=max(120, min(900, n * 120)),
            temperature=0.2,
            messages=[
                {"role": "system", "content": _candidate_prompt(ctx, n)},
                {"role": "user", "content": natural_language},
            ],
        )
    except OpenAIError as exc:
        raise LlmError(f"LLM request failed: {exc}") from exc

    content = resp.choices[0].message.content or ""
    return parse_candidate_commands(content, n)


def parse_candidate_commands(text: str, n: int) -> list[str]:
    cleaned = strip_fences(text)
    commands: list[str] = []
    for line in cleaned.splitlines():
        command = strip_fences(line)
        if command:
            commands.append(command)
        if len(commands) >= n:
            break
    return commands


def _candidate_prompt(ctx: str, n: int) -> str:
    return (
        build_system_prompt(ctx)
        + "\n"
        + f"Return exactly {n} distinct shell command candidates, one per line.\n"
        + "Do not number them. Do not explain. Do not include markdown fences."
    )


def explain_command(command: str, cfg: AskConfig) -> str:
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    try:
        resp = client.chat.completions.create(
            model=cfg.model,
            max_tokens=500,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You explain shell commands for a careful terminal user."},
                {"role": "user", "content": build_explain_prompt(command)},
            ],
        )
    except OpenAIError as exc:
        raise LlmError(f"LLM request failed: {exc}") from exc

    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise LlmError("LLM returned an empty explanation.")
    return content


def gen_next_step(
    original_nl: str,
    command: str,
    result: str,
    ctx: str,
    cfg: AskConfig,
) -> str:
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    try:
        resp = client.chat.completions.create(
            model=cfg.model,
            max_tokens=300,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a shell assistant. The user ran a command. "
                        "Suggest the single most useful next shell command based on the output. "
                        "Output only the command, no explanation. Never include markdown fences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original task:\n{original_nl}\n\n"
                        f"Command run:\n{command}\n\n"
                        f"Command output:\n{result}\n\n"
                        f"Context:\n{ctx}"
                    ),
                },
            ],
        )
    except OpenAIError as exc:
        raise LlmError(f"LLM request failed: {exc}") from exc

    next_command = strip_fences(resp.choices[0].message.content or "")
    if not next_command:
        raise LlmError("LLM returned an empty next command.")
    return next_command


def strip_fences(text: str) -> str:
    cleaned = text.strip()
    fence = re.fullmatch(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()

    lines = [line.rstrip() for line in cleaned.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()
