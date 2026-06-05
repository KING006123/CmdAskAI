# CmdAskAI — `ask`

> Type a sentence in plain language, get the exact shell command for **your** system — reviewed by you before it ever runs.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](#cross-platform)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Provider](https://img.shields.io/badge/LLM-OpenAI--compatible-orange.svg)](#configuration)

`ask` turns natural language into a shell command, shows it to you with syntax highlighting, and **only runs it after you confirm**. It is not a history-search trick or a fixed cheat-sheet — the command is generated live by an LLM that is told about your actual OS, shell, current directory, and recent workflow, so the flags are correct for *your* machine instead of a generic Linux example.

```text
$ ask "find python files changed in the last two days"

╭─ Generated command ──────────────────────────────────────╮
│ find . -name "*.py" -mtime -2                            │
╰──────────────────────────────────────────────────────────╯
Actions: [r]un  [e]dit  [c]opy  e[x]plain  [d]ry-run  [q]uit
```

---

## Why it's different

Most "AI in the terminal" tools either correct your last command or look up a static cheat sheet. `ask` does three things they don't:

- **Commands are generated live**, not retrieved — it adapts to whatever you actually ask.
- **It knows your system.** macOS vs. Linux flag differences (`sed -i`, `stat`, `date`, `find`) are the line between *useful* and *broken*; `ask` sends the real OS + shell as context and asks for BSD/macOS-compatible flags when they differ.
- **Safety is the default, not an afterthought.** Nothing auto-runs. Dangerous commands are detected, flagged in red, gated behind a second confirmation, and can be previewed with a non-destructive dry-run hint.

---

## Features

| Feature | What it does |
|---|---|
| **Live NL → command** | One sentence in, one correct command out. |
| **System-aware context** | OS, shell, cwd, available tools, git status, project hints, recent files. |
| **Never auto-runs** | Always shows → confirms → runs. Hard safety line. |
| **Danger detection + dry-run** | Flags `rm -rf`, `dd`, `mkfs`, fork bombs, `Format-Volume`, etc. Offers a safe preview command. |
| **Multiple candidates** | `--candidates N` generates N options and lets you pick. |
| **History personalization** | Reads recent (secret-filtered) shell history to understand "continue", "this", "刚才". |
| **Result feedback loop** | After a command runs, type a follow-up; the output is fed back for the next step. |
| **Explain** | `-e` explains what a command does, its risks, and how to undo it (in Simplified Chinese). |
| **`Ctrl+G` inline replace** | Type plain language at the prompt, press `Ctrl+G`, the line is replaced in place. |
| **Cross-platform** | macOS / Linux (zsh, bash) and Windows (PowerShell). |
| **Provider-agnostic** | Any OpenAI-compatible endpoint — DeepSeek, OpenAI, Ollama, OpenRouter. |

---

## Install

```bash
git clone https://github.com/KING006123/CmdAskAI.git
cd CmdAskAI
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

> **macOS note:** keep the project **out of iCloud-synced folders** (`~/Documents`, `~/Desktop`). iCloud sets a hidden flag on files inside `.venv`, and Python 3.14 skips hidden `.pth` files — which silently breaks editable installs. Use `~/Projects` or similar.

To make `ask` available everywhere without activating the venv, symlink it onto your `PATH`:

```bash
ln -sf "$(pwd)/.venv/bin/ask" ~/.local/bin/ask
```

---

## Configuration

Create `~/.config/ask/config.toml` (macOS/Linux) or `%APPDATA%\ask\config.toml` (Windows):

```toml
[provider]
name = "deepseek"
base_url = "https://api.deepseek.com"
model = "deepseek-chat"
# api_key = "..."   # prefer the environment variable below

[ui]
default_action = "ask"
history_lines = 20   # recent shell commands sent as context (0 to disable)
candidates = 1       # default number of candidates to generate
```

Provide the API key via environment variable (never committed):

```bash
export ASK_API_KEY="your_api_key"
# or provider-specific:
export DEEPSEEK_API_KEY="..."
export OPENAI_API_KEY="..."
```

**Switching providers is three lines** — point `base_url`/`model` at OpenAI, a local Ollama server, or OpenRouter; the code is unchanged.

---

## Usage

```bash
ask "list files by size"                 # interactive: review, then choose an action
ask --candidates 3 "compress this folder"  # generate 3 options and pick one
ask -e "lsof -i :8080"                   # explain an existing command
ask --raw "show listening ports"         # print only the command (for scripts / Ctrl+G)
ask --debug-context                      # show the safe context sent to the model
ask --export-config                      # print a shareable config with the key redacted
```

Interactive actions: **r**un · **e**dit · **c**opy · e**x**plain · **d**ry-run (dangerous commands) · **q**uit.

### `Ctrl+G` inline replace

Source the integration for your shell, then type plain language at the prompt and press `Ctrl+G` — the current line is replaced with the generated command, ready to edit or run.

```bash
# zsh
source /path/to/CmdAskAI/shell/ask.zsh
# bash
source /path/to/CmdAskAI/shell/ask.bash
```

```powershell
# PowerShell — add to your profile
. "C:\path\to\CmdAskAI\shell\ask.ps1"
```

---

## How it works

```text
ask "natural language"
  → load config (provider / base_url / key / model)
  → collect safe context (OS, shell, cwd, tools, git, recent files & history)
  → build prompt → call LLM → strip code fences → clean command
  → safety scan (rm -rf, dd, mkfs, Format-Volume, ...)
  → show command (highlighted) + danger flags + dry-run hint
  → action menu: run / edit / copy / explain / dry-run / quit
  → (after run) optional follow-up → feed output back → next command
```

**Secrets never leave your machine:** environment variables, `.env` files, and history lines containing `key`, `token`, `secret`, `password`, `export ...` are filtered out before any context is sent.

---

## Cross-platform

A small `ask/platform/` layer abstracts the OS-specific bits so the rest of the code stays clean:

| | macOS / Linux | Windows |
|---|---|---|
| Shell | zsh / bash | PowerShell / cmd |
| Run command | `sh -c` | `powershell -Command` / `cmd /c` |
| Config dir | `~/.config/ask` | `%APPDATA%\ask` |
| History | `~/.zsh_history`, `~/.bash_history` | PSReadLine history |
| Danger hints | `diskutil`, `ls -la` | `Get-Disk`, `Get-ChildItem` |

---

## Project structure

```text
ask/
├── cli.py          # argument parsing + main action loop
├── llm.py          # OpenAI-compatible client, command/candidate/next-step generation
├── context.py      # collect safe system & workflow context
├── prompt.py       # system + explain prompts
├── safety.py       # dangerous-command detection + dry-run hints
├── history.py      # recent shell history (secret-filtered)
├── runner.py       # run / edit / copy
├── ui.py           # rich rendering + action menus
├── config.py       # TOML + env config loading
└── platform/       # unix / windows abstraction
shell/              # ask.zsh · ask.bash · ask.ps1 (Ctrl+G)
tests/              # pytest suite
```

---

## Development

```bash
python -m pytest          # run the test suite
ask --debug-context       # inspect exactly what context is sent
```

## Building standalone binaries

```bash
python -m pip install -e ".[build]"
pyinstaller ask.spec      # → dist/ask (macOS/Linux) or dist/ask.exe (Windows)
```

Tagging a release builds downloadable artifacts via GitHub Actions:

```bash
git tag v0.1.0 && git push origin v0.1.0
# → ask-macos-latest-full.tar.gz · ask-ubuntu-latest-full.tar.gz · ask-windows.zip
```

---

## Roadmap

- [x] Multiple command candidates
- [x] Shell history personalization
- [x] Dangerous-command dry-run hints
- [x] Execution-result feedback loop
- [x] Cross-platform (macOS / Linux / Windows)
- [ ] Streaming + spinner to cut perceived latency
- [ ] Personal command knowledge base (semantic recall of your own commands)
- [ ] Multi-language natural-language input

---

## License

[MIT](LICENSE) © 2026 KING006123
