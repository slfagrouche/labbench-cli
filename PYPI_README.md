# LabBench

Production-grade terminal AI assistant for Python, notebooks, and data workflows.

## Install

```bash
python3 -m pip install --upgrade pip
python3 -m pip install labbench-cli
```

## Quick start

Set one provider API key before first run:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

Then run:

```bash
labbench
```

## Usage

```bash
labbench -m gpt-4o
labbench -m claude-opus-4-6
labbench -m ollama/qwen2.5-coder
labbench -p "Summarize this repository"
```

## What it includes

- Terminal-first interactive REPL
- One-shot automation mode
- Safe file and shell tooling
- Notebook editing, web fetch/search, diagnostics
- Memory and skill systems for persistent workflows

## Links

- Repository: https://github.com/slfagrouche/labbench-cli
- License: Apache-2.0
