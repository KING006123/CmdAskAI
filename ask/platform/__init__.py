from __future__ import annotations

import sys

if sys.platform == "win32":
    from ask.platform.windows import get_config_dir
    from ask.platform.windows import get_context_info
    from ask.platform.windows import get_history_file
    from ask.platform.windows import get_shell
    from ask.platform.windows import run_shell_command
else:
    from ask.platform.unix import get_config_dir
    from ask.platform.unix import get_context_info
    from ask.platform.unix import get_history_file
    from ask.platform.unix import get_shell
    from ask.platform.unix import run_shell_command

__all__ = [
    "get_config_dir",
    "get_context_info",
    "get_history_file",
    "get_shell",
    "run_shell_command",
]

