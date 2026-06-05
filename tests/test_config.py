from pathlib import Path
from unittest.mock import patch

from ask.config import load_config


def test_load_config_reads_v2_ui_fields(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[provider]\n"
        'name = "deepseek"\n'
        'base_url = "https://api.deepseek.com"\n'
        'api_key = "config-key"\n'
        'model = "deepseek-chat"\n'
        "\n"
        "[ui]\n"
        'default_action = "ask"\n'
        "history_lines = 7\n"
        "candidates = 3\n"
    )

    with patch.dict("os.environ", {"ASK_API_KEY": "test-key"}):
        cfg = load_config(config)

    assert cfg.history_lines == 7
    assert cfg.candidates == 3
    assert cfg.api_key == "test-key"


def test_load_config_can_read_api_key_from_toml(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[provider]\n"
        'name = "deepseek"\n'
        'base_url = "https://api.deepseek.com"\n'
        'api_key = "config-key"\n'
        'model = "deepseek-chat"\n'
    )

    with patch.dict("os.environ", {}, clear=True):
        cfg = load_config(config)

    assert cfg.api_key == "config-key"


def test_load_config_can_skip_required_api_key(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[provider]\n"
        'name = "deepseek"\n'
        'base_url = "https://api.deepseek.com"\n'
        'model = "deepseek-chat"\n'
    )

    with patch.dict("os.environ", {}, clear=True):
        cfg = load_config(config, require_api_key=False)

    assert cfg.api_key == ""
