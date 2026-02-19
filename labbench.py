#!/usr/bin/env python3
"""
LabBench — small terminal AI for notebooks, data, and Python.

Usage:
  python labbench.py [options] [prompt]

Options:
  -p, --print          Non-interactive: run prompt and exit (also --print-output)
  -m, --model MODEL    Override model
  --accept-all         Never ask permission (dangerous)
  --verbose            Show thinking + token counts
  --version            Print version and exit

Slash commands in REPL:
  /help       Show this help
  /clear      Clear conversation
  /model [m]  Show or set model
  /config     Show config / set key=value
  /save [f]   Save session to file
  /load [f]   Load session from file
  /history    Print conversation history
  /context    Show context window usage
  /cost       Show API cost this session
  /verbose    Toggle verbose mode
  /thinking   Toggle extended thinking
  /permissions [mode]  Set permission mode
  /cwd [path] Show or change working directory
  /memory [query]   Show/search persistent memories
  /skills           List available skills
  /resume           Load latest autosaved session
  /eda /notebook    EDA & notebook workflow (built-in skill)
  /exit /quit Exit
"""
from __future__ import annotations

import os
import sys
import json
try:
    import readline
except ImportError:
    readline = None  # Windows compatibility
import atexit
import argparse
from pathlib import Path
from datetime import datetime
from typing import Union

# ── Optional rich for markdown rendering ──────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    _RICH = True
    console = Console()
except ImportError:
    _RICH = False
    console = None

VERSION = "0.1.0"

# ── ANSI helpers (used even with rich for non-markdown output) ─────────────
C = {
    "cyan":    "\033[36m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "red":     "\033[31m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "reset":   "\033[0m",
}

def clr(text: str, *keys: str) -> str:
    return "".join(C[k] for k in keys) + str(text) + C["reset"]

def info(msg: str):   print(clr(msg, "cyan"))
def ok(msg: str):     print(clr(msg, "green"))
def warn(msg: str):   print(clr(f"Warning: {msg}", "yellow"))
def err(msg: str):    print(clr(f"Error: {msg}", "red"), file=sys.stderr)


def _use_rich_banner() -> bool:
    return bool(_RICH and console and sys.stdout.isatty() and not os.environ.get("NO_COLOR"))


def print_welcome_banner(config: dict) -> None:
    """Startup banner: Rich panel when available, else ANSI box."""
    from providers import detect_provider

    model = config["model"]
    pname = detect_provider(model)
    pmode = config.get("permission_mode", "auto")
    if _use_rich_banner():
        body = (
            f"[bold cyan]{model}[/] [dim]({pname})[/]\n"
            f"Permissions: [yellow]{pmode}[/]\n"
            f"[dim]/model · /help · notebooks · data[/]"
        )
        console.print(
            Panel.fit(
                body,
                title="[bold bright_cyan]LabBench[/]",
                subtitle="[dim]terminal · notebooks · python[/]",
                border_style="cyan",
            )
        )
        print()
        return
    model_clr = clr(model, "cyan", "bold")
    prov_clr = clr(f"({pname})", "dim")
    pmode_c = clr(pmode, "yellow")
    print(clr("╭─ LabBench — notebooks · data · python ────╮", "cyan", "bold"))
    print(clr("│  Model: ", "dim") + model_clr + " " + prov_clr)
    print(clr("│  Permissions: ", "dim") + pmode_c)
    print(clr("│  /model · /help                                  │", "dim"))
    print(clr("╰──────────────────────────────────────────────────╯", "dim"))
    print()


def render_diff(text: str):
    """Print diff text with ANSI colors: red for removals, green for additions."""
    for line in text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            print(C["bold"] + line + C["reset"])
        elif line.startswith("+"):
            print(C["green"] + line + C["reset"])
        elif line.startswith("-"):
            print(C["red"] + line + C["reset"])
        elif line.startswith("@@"):
            print(C["cyan"] + line + C["reset"])
        else:
            print(line)

def _has_diff(text: str) -> bool:
    """Check if text contains a unified diff."""
    return "--- a/" in text and "+++ b/" in text


# ── Conversation rendering ─────────────────────────────────────────────────

_accumulated_text: list[str] = []   # buffer text during streaming

def stream_text(chunk: str):
    """Called for each streamed text chunk."""
    print(chunk, end="", flush=True)
    _accumulated_text.append(chunk)

def stream_thinking(chunk: str, verbose: bool):
    if verbose:
        print(clr(chunk, "dim"), end="", flush=True)

def flush_response():
    """After streaming, optionally re-render as markdown."""
    full = "".join(_accumulated_text)
    _accumulated_text.clear()
    if _RICH and full.strip():
        # Re-print with markdown rendering
        print("\r", end="")      # go to line start to overwrite last newline
        # only re-render if there's actual markdown (contains # * ` _ etc.)
        if any(c in full for c in ("#", "*", "`", "_", "[")):
            print()   # newline after streaming
            console.print(Markdown(full))
            return
    print()  # ensure newline after stream

def print_tool_start(name: str, inputs: dict, verbose: bool):
    """Show tool invocation."""
    desc = _tool_desc(name, inputs)
    print(clr(f"\n  ⚙  {desc}", "dim", "cyan"), flush=True)
    if verbose:
        print(clr(f"     inputs: {json.dumps(inputs, ensure_ascii=False)[:200]}", "dim"))

def print_tool_end(name: str, result: str, verbose: bool):
    lines = result.count("\n") + 1
    size = len(result)
    summary = f"→ {lines} lines ({size} chars)"
    if not result.startswith("Error") and not result.startswith("Denied"):
        print(clr(f"  ✓ {summary}", "dim", "green"), flush=True)
        # Render diff for Edit/Write results
        if name in ("Edit", "Write") and _has_diff(result):
            parts = result.split("\n\n", 1)
            if len(parts) == 2:
                print(clr(f"  {parts[0]}", "dim"))
                render_diff(parts[1])
    else:
        print(clr(f"  ✗ {result[:120]}", "dim", "red"), flush=True)
    if verbose and not result.startswith("Denied"):
        preview = result[:500] + ("…" if len(result) > 500 else "")
        print(clr(f"     {preview.replace(chr(10), chr(10)+'     ')}", "dim"))

def _tool_desc(name: str, inputs: dict) -> str:
    if name == "Read":   return f"Read({inputs.get('file_path','')})"
    if name == "Write":  return f"Write({inputs.get('file_path','')})"
    if name == "Edit":   return f"Edit({inputs.get('file_path','')})"
    if name == "Bash":   return f"Bash({inputs.get('command','')[:80]})"
    if name == "Glob":   return f"Glob({inputs.get('pattern','')})"
    if name == "Grep":   return f"Grep({inputs.get('pattern','')})"
    if name == "WebFetch":    return f"WebFetch({inputs.get('url','')[:60]})"
    if name == "WebSearch":   return f"WebSearch({inputs.get('query','')})"
    return f"{name}({list(inputs.values())[:1]})"


# ── Permission prompt ──────────────────────────────────────────────────────

def ask_permission_interactive(desc: str, config: dict) -> bool:
    try:
        print()
        ans = input(clr(f"  Allow: {desc}  [y/N/a(ccept-all)] ", "yellow")).strip().lower()
        if ans == "a":
            config["permission_mode"] = "accept-all"
            ok("  Permission mode set to accept-all for this session.")
            return True
        return ans in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        print()
        return False


# ── Slash commands ─────────────────────────────────────────────────────────

def cmd_help(_args: str, _state, _config) -> bool:
    print(__doc__)
    return True

def cmd_clear(_args: str, state, _config) -> bool:
    state.messages.clear()
    state.turn_count = 0
    ok("Conversation cleared.")
    return True

def cmd_model(args: str, _state, config) -> bool:
    from providers import PROVIDERS, detect_provider
    if not args:
        model = config["model"]
        pname = detect_provider(model)
        info(f"Current model:    {model}  (provider: {pname})")
        info("\nAvailable models by provider:")
        for pn, pdata in PROVIDERS.items():
            ms = pdata.get("models", [])
            if ms:
                info(f"  {pn:12s}  " + ", ".join(ms[:4]) + ("..." if len(ms) > 4 else ""))
        info("\nFormat: 'provider/model' or just model name (auto-detected)")
        info("  e.g. /model gpt-4o")
        info("  e.g. /model ollama/qwen2.5-coder")
        info("  e.g. /model kimi:moonshot-v1-32k")
    else:
        # Accept both "ollama/model" and "ollama:model" syntax
        m = args.strip().replace(":", "/", 1)
        config["model"] = m
        pname = detect_provider(m)
        ok(f"Model set to {m}  (provider: {pname})")
        from config import save_config
        save_config(config)
    return True

def cmd_config(args: str, _state, config) -> bool:
    from config import save_config
    if not args:
        display = {k: v for k, v in config.items() if k != "api_key"}
        print(json.dumps(display, indent=2))
    elif "=" in args:
        key, _, val = args.partition("=")
        key, val = key.strip(), val.strip()
        # Type coercion
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        elif val.isdigit():
            val = int(val)
        config[key] = val
        save_config(config)
        ok(f"Set {key} = {val}")
    else:
        k = args.strip()
        v = config.get(k, "(not set)")
        info(f"{k} = {v}")
    return True

def cmd_save(args: str, state, _config) -> bool:
    from config import SESSIONS_DIR
    fname = args.strip() or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = Path(fname) if "/" in fname else SESSIONS_DIR / fname
    data = {
        "messages": [
            m if not isinstance(m.get("content"), list) else
            {**m, "content": [
                b if isinstance(b, dict) else b.model_dump()
                for b in m["content"]
            ]}
            for m in state.messages
        ],
        "turn_count": state.turn_count,
        "total_input_tokens": state.total_input_tokens,
        "total_output_tokens": state.total_output_tokens,
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    ok(f"Session saved to {path}")
    return True

def save_latest(args: str, state, _config) -> bool:
    from config import MR_SESSION_DIR
    fname = "session_latest.json"
    path = Path(fname) if "/" in fname else MR_SESSION_DIR / fname
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "messages": [
            m if not isinstance(m.get("content"), list) else
            {**m, "content": [
                b if isinstance(b, dict) else b.model_dump()
                for b in m["content"]
            ]}
            for m in state.messages
        ],
        "turn_count": state.turn_count,
        "total_input_tokens": state.total_input_tokens,
        "total_output_tokens": state.total_output_tokens,
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    ok(f"Session saved to {path}")
    return True
def cmd_load(args: str, state, _config) -> bool:
    from config import SESSIONS_DIR
    if not args.strip():
        # List available sessions
        sessions = sorted(SESSIONS_DIR.glob("*.json"))
        if not sessions:
            info("No saved sessions found.")
        else:
            info("Saved sessions:")
            for s in sessions:
                info(f"  {s.name}")
        return True
    fname = args.strip()
    path = Path(fname) if "/" in fname else SESSIONS_DIR / fname
    if not path.exists():
        err(f"File not found: {path}")
        return True
    data = json.loads(path.read_text())
    state.messages = data.get("messages", [])
    state.turn_count = data.get("turn_count", 0)
    state.total_input_tokens = data.get("total_input_tokens", 0)
    state.total_output_tokens = data.get("total_output_tokens", 0)
    ok(f"Session loaded from {path} ({len(state.messages)} messages)")
    return True
