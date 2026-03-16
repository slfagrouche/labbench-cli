# Contributor Guide: Where to Change What in LabBench

This guide is for contributors implementing new features or updating existing behavior.
It focuses on **which files matter**, **how data flows**, and **how to make safe changes quickly**.

---

## 1) Fast mental model

If you remember only one thing, remember this flow:

1. `labbench.py` handles CLI + REPL + slash commands.
2. `context.py` rebuilds the system prompt each turn.
3. `agent.py` runs the core loop (stream model output, execute tools, append tool results, continue).
4. `providers.py` adapts model APIs (Anthropic vs OpenAI-compatible providers).
5. `tool_registry.py` is the single source of truth for all callable tools.
6. Feature packages (`memory/`, `skill/`) plug into that loop.

---

## 2) Core files you should read first

### Runtime + UX shell
- `labbench.py`
  - Entry point (`main()`), REPL loop (`repl()`), command dispatch (`COMMANDS`, `handle_slash()`), permission prompt UI, diff rendering.
  - Add or change slash commands here.

### Agent execution loop
- `agent.py`
  - `run(...)` generator is the heart of the app.
  - Event model: `TextChunk`, `ThinkingChunk`, `ToolStart`, `ToolEnd`, `PermissionRequest`, `TurnDone`.
  - Permission gate logic (`_check_permission`) and per-turn context compaction trigger.

### Tool system
- `tool_registry.py`
  - `ToolDef`, `register_tool`, `get_tool_schemas`, and centralized `execute_tool` dispatch/truncation.
  - Every tool (built-in plus memory/skill package tools) ends up here.

- `tools.py`
  - Core built-in tool schemas and implementations (`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `NotebookEdit`, `GetDiagnostics`, `AskUserQuestion`).
  - `_register_builtins()` registers core tools, then imports package tool modules to auto-register additional tools.

### Model providers + prompt context + compaction
- `providers.py` — provider detection, model metadata, API key lookup, stream adapters, neutral message format conversion.
- `context.py` — system prompt assembly (git info, `CLAUDE.md`, memory injection).
- `compaction.py` — context window management (`snip_old_tool_results` + `compact_messages`).
- `config.py` — defaults + persistent config file handling.

---

## 3) Feature packages: exact entrypoints

## Memory (`memory/`)
- Start at `memory/tools.py` (tool behavior and schemas).
- Persistence/index rules are in `memory/store.py`.
- Memory retrieval/ranking context is in `memory/context.py`.
- Metadata scanning and freshness helpers are in `memory/scan.py`.

Use this package when adding memory types, changing indexing, staleness behavior, or search behavior.

## Skills (`skill/`)
- `skill/loader.py` parses markdown frontmatter and resolves project/user/builtin precedence (kebab-case keys like `when-to-use` are accepted).
- `skill/builtin.py` registers built-in skills (`/commit`, `/review`, `/eda`, `/notebook`, etc.).
- `skill/executor.py` runs inline vs forked skill execution.
- `skill/tools.py` exposes `Skill` and `SkillList` tool APIs.

Use this package when adding skill metadata fields, argument substitution behavior, or skill execution modes. There is **no** top-level `skills.py` — import from the `skill` package only.

---

## 4) “I need to implement X” → where to edit

### Add a new built-in tool
1. Add schema + implementation in `tools.py`.
2. Register in `_register_builtins()` as a `ToolDef`.
