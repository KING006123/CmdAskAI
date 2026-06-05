from ask.prompt import build_explain_prompt
from ask.prompt import build_system_prompt


def test_explain_prompt_requires_simplified_chinese() -> None:
    prompt = build_explain_prompt("ls -la")

    assert "Simplified Chinese" in prompt
    assert "它做什么" in prompt


def test_system_prompt_uses_richer_context_rules() -> None:
    prompt = build_system_prompt("OS: macOS\nProject hints:\n- Python project")

    assert "terminal context" in prompt
    assert "project hints" in prompt
    assert "ambiguous" in prompt
    assert "BSD/macOS-compatible" in prompt
