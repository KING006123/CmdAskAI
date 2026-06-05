from ask.cli import _export_config
from ask.config import AskConfig


def test_export_config_redacts_api_key() -> None:
    cfg = AskConfig(
        provider="deepseek",
        base_url="https://api.deepseek.com",
        api_key="real-secret",
        model="deepseek-chat",
        history_lines=20,
        candidates=2,
    )

    exported = _export_config(cfg)

    assert "real-secret" not in exported
    assert 'api_key = "YOUR_API_KEY_HERE"' in exported
    assert "history_lines = 20" in exported
    assert "candidates = 2" in exported

