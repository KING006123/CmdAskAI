from ask.safety import inspect_command


def test_flags_force_remove_root() -> None:
    result = inspect_command("sudo rm -rf /")
    assert result.dangerous
    assert result.dry_run_hint is not None


def test_allows_read_only_command() -> None:
    result = inspect_command("find . -name '*.py' -mtime -2")
    assert not result.dangerous
    assert result.dry_run_hint is None


def test_dry_run_hint_for_recursive_chmod() -> None:
    result = inspect_command("chmod -R 777 uploads")

    assert result.dangerous
    assert result.dry_run_hint == "ls -la <target>  # check current permissions"
