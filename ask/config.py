from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from ask.platform import get_config_dir

DEFAULT_CONFIG_PATH = get_config_dir() / "config.toml"


@dataclass(frozen=True)
class AskConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    default_action: str = "ask"
    history_lines: int = 20
    candidates: int = 1


class ConfigError(RuntimeError):
    """Raised when ask cannot load a usable provider configuration."""


def load_config(path: Path | None = None, require_api_key: bool = True) -> AskConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    raw = _load_toml(config_path)
    provider_data = raw.get("provider", {})
    ui_data = raw.get("ui", {})

    provider = _env("ASK_PROVIDER") or str(provider_data.get("name") or "deepseek")
    base_url = _env("ASK_BASE_URL") or str(provider_data.get("base_url") or "https://api.deepseek.com")
    model = _env("ASK_MODEL") or str(provider_data.get("model") or "deepseek-chat")
    api_key = _find_api_key(provider, provider_data)

    if require_api_key and not api_key:
        raise ConfigError(
            "Missing API key. Set ASK_API_KEY or a provider key such as DEEPSEEK_API_KEY."
        )

    return AskConfig(
        provider=provider,
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        default_action=str(ui_data.get("default_action") or "ask"),
        history_lines=_int_value(ui_data.get("history_lines"), 20),
        candidates=_int_value(ui_data.get("candidates"), 1),
    )


def _load_toml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}

    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid config file at {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid config shape at {path}.")
    return data


def _find_api_key(provider: str, provider_data: dict[str, object]) -> str:
    provider_env = f"{provider.upper().replace('-', '_')}_API_KEY"
    config_key = str(provider_data.get("api_key") or "").strip()
    return _env("ASK_API_KEY") or _env(provider_env) or _env("OPENAI_API_KEY") or config_key


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _int_value(value: object, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise ConfigError(f"Invalid integer value: {value}") from exc
    raise ConfigError(f"Invalid integer value: {value}")
