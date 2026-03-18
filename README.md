# LabBench

LabBench is an open-source, production-oriented terminal AI assistant for Python, notebooks, and data workflows.
It is intentionally compact, with practical safeguards and operational features for real projects.

## Overview

- Terminal-first workflow with minimal moving parts
- Works in any repository directory (`./.labbench/` for project-local state)
- Supports hosted and local model providers through one interface
- Includes permission controls, tool safety gates, memory, skills, diagnostics, and tests

## Visual Architecture

### 1) End-to-end flow (for technical and non-technical readers)

![End-to-end flow](docs/diagrams/end_to_end_flow.png)

Interpretation:
- Non-technical: user asks, system runs safely, user gets result.
- Technical: agent orchestrates provider calls, tool execution, memory/skills, and permission checks.

### 2) Permission model (production safety)

![Permission model](docs/diagrams/permission_model.png)

### 3) Runtime components (technical map)

![Runtime components](docs/diagrams/runtime_components.png)

### Interactive Excalidraw diagrams

- End-to-end architecture (interactive): [Open diagram](https://excalidraw.com/#json=bqXvrlE3dNHYn45ZRV06q,rILNOg8u_Jx2QmtCnsfyTA)
- Permission decision flow (interactive): [Open diagram](https://excalidraw.com/#json=uS3yu8fc5PCPCYosxSyks,Ff1lRFB1H7bqQNZVt7_JdA)

## Quick Start

```bash
git clone <your-repo-url> labbench
cd labbench
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python3 -m pip install -r requirements.txt
python3 labbench.py
```

Set one of these API keys before first run (depending on provider):
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- provider-specific keys for other backends in `providers.py`

## Supported Providers

LabBench supports both hosted and local providers through a unified interface.

### Hosted providers
- `anthropic` (Claude)
- `openai` (GPT/o-series)
- `gemini` (Google Gemini via OpenAI-compatible endpoint)
- `kimi` (Moonshot)
- `qwen` (DashScope)
- `zhipu` (GLM)
- `deepseek` (DeepSeek)
- `custom` (any OpenAI-compatible API via `custom/<model>`)

### Local/self-hosted providers
- `ollama` (local server, no cloud key required)
- `lmstudio` (local server, no cloud key required)

Use either:
- Auto-detected model names (example: `claude-opus-4-6`, `gpt-4o`)
- Explicit prefix form (example: `ollama/qwen2.5-coder`, `custom/my-model`)

For exact env var mapping and defaults, see `providers.py`.

## Production Usage

### Interactive (default REPL)

```bash
python3 labbench.py
```

### Interactive with explicit provider/model

```bash
