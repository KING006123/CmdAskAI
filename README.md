# ask

`ask` is a local terminal helper that turns natural language into a shell command, shows it to you, and only runs it after confirmation.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Configure

Create `~/.config/ask/config.toml` on macOS/Linux or `%APPDATA%\ask\config.toml` on Windows:

```toml
[provider]
name = "deepseek"
base_url = "https://api.deepseek.com"
model = "deepseek-chat"
```

Set the key in your shell:

```bash
export ASK_API_KEY="your_api_key"
```

You can also use provider-specific variables:

```bash
export DEEPSEEK_API_KEY="your_deepseek_key"
export OPENAI_API_KEY="your_openai_key"
```

## Use

```bash
ask "find python files changed in the last two days"
ask --raw "list files by size"
ask --explain "show listening ports"
```

Interactive mode never auto-runs a generated command. It shows the command first, then lets you run, edit, copy, explain, or cancel.

On macOS, `ask` sends macOS context to the model and asks for BSD/macOS-compatible flags when Linux and macOS commands differ.

## Shell Shortcut

For zsh:

```bash
source /path/to/ask/shell/ask.zsh
```

For bash:

```bash
source /path/to/ask/shell/ask.bash
```

Then type natural language at the prompt and press `Ctrl+G`. The current line is replaced with the generated command.

For PowerShell on Windows:

```powershell
. "C:\path\to\ask\shell\ask.ps1"
```

Add that line to your PowerShell profile to enable `Ctrl+G` permanently.

## Binary Builds

Install build dependencies:

```bash
python -m pip install -e ".[build]"
```

Build the current platform binary:

```bash
pyinstaller ask.spec
```

The executable is written to `dist/ask` on macOS/Linux and `dist/ask.exe` on Windows.

## GitHub Release

Tag a release to build downloadable artifacts:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The release workflow builds:

```text
ask-ubuntu-latest-full.tar.gz
ask-macos-latest-full.tar.gz
ask-windows.zip
```
