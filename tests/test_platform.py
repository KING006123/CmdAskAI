from pathlib import Path
from unittest.mock import patch

from ask.platform import unix
from ask.platform import windows


def test_unix_config_dir_uses_xdg_config_home() -> None:
    with patch.dict("os.environ", {"XDG_CONFIG_HOME": "/tmp/config"}):
        assert unix.get_config_dir() == Path("/tmp/config/ask")


def test_windows_config_dir_uses_appdata() -> None:
    with patch.dict("os.environ", {"APPDATA": r"C:\Users\me\AppData\Roaming"}):
        assert windows.get_config_dir() == Path(r"C:\Users\me\AppData\Roaming") / "ask"


def test_windows_shell_detects_powershell() -> None:
    with patch.dict("os.environ", {"PSModulePath": "modules"}):
        assert windows.get_shell() == "powershell"

