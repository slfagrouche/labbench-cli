# Architecture Guide

This document is for developers who want to understand, modify, or extend LabBench.
For user-facing docs, see [README.md](../README.md).

---

## Overview

LabBench is a Python terminal assistant that lets LLMs (Claude, GPT, Gemini, local models, etc.)
drive tools, memory, and skills with a focus on notebooks and data workflows. The
codebase uses a flat module layout for readability.

```
User Input
    │
    ▼
labbench.py  ── REPL, slash commands, rendering
    │
    ├──► agent.py  ── multi-turn loop, permission gates
    │       │
    │       ├──► providers.py  ── API streaming (Anthropic / OpenAI-compat)
    │       ├──► tool_registry.py ──► tools.py  ── built-ins + memory/skill tools
    │       ├──► compaction.py  ── context window management
    │
    ├──► context.py  ── system prompt (git, CLAUDE.md, memory)
    │       └──► memory/  ── persistent file-based memory
    │
    ├──► skill/  ── markdown skills (loader, builtins, tools, executor)
    └──► config.py  ── configuration persistence
```

**Key invariant:** Dependencies flow downward. No circular imports at the module level.

---

## Module Reference

### `tool_registry.py` — Tool Registry

The central registry that all tools register into. This is the foundation for extensibility.

**Data model:**

```python
@dataclass
class ToolDef:
    name: str               # unique identifier (e.g. "Read", "MemorySave")
    schema: dict            # JSON schema sent to the LLM API
    func: Callable          # (params: dict, config: dict) -> str
    read_only: bool         # True = auto-approve in 'auto' permission mode
    concurrent_safe: bool   # True = safe to run in parallel
```

**Public API:**

| Function | Description |
|---|---|
| `register_tool(tool_def)` | Add a tool to the registry (overwrites by name) |
| `get_tool(name)` | Look up by name, returns `None` if not found |
| `get_all_tools()` | List all registered tools |
| `get_tool_schemas()` | Return schemas for API calls |
| `execute_tool(name, params, config, max_output=32000)` | Execute with output truncation |
| `clear_registry()` | Reset — for testing only |

**Output truncation:** If a tool returns more than `max_output` chars, the result is
truncated to `first_half + [... N chars truncated ...] + last_quarter`. This prevents
a single tool call (e.g. reading a huge file) from blowing up the context window.

**Registering a custom tool:**

```python
from tool_registry import ToolDef, register_tool

def my_tool(params, config):
    return f"Hello, {params['name']}!"

register_tool(ToolDef(
    name="MyTool",
    schema={
        "name": "MyTool",
        "description": "A greeting tool",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    func=my_tool,
    read_only=True,
    concurrent_safe=True,
))
```

### `tools.py` — Built-in Tool Implementations

Contains core built-in tools (Read/Write/Edit/Bash/Glob/Grep/WebFetch/WebSearch/NotebookEdit/GetDiagnostics/AskUserQuestion),
then imports `memory.tools` and `skill.tools` so memory/skill tools auto-register via `tool_registry`.

**Key internals:**

- `_is_safe_bash(cmd)` — whitelist of safe shell commands for auto-approval
- `generate_unified_diff(old, new, filename)` — diff generation for Edit/Write
- `maybe_truncate_diff(diff_text, max_lines=80)` — truncate large diffs for display
- Backward-compatible `execute_tool(name, inputs, permission_mode, ask_permission)` wrapper

### `agent.py` — Core Agent Loop

The heart of the system. `run()` is a generator that yields events as they happen.

```python
def run(user_message, state, config, system_prompt,
        depth=0, cancel_check=None) -> Generator:
```

**Loop logic:**

```
1. Append user message
2. Inject depth metadata into config
3. While True:
   a. Check cancel_check() (if provided)
   b. maybe_compact(state, config) — compress if near context limit
   c. Stream from provider → yield TextChunk / ThinkingChunk
   d. Record assistant message
   e. If no tool_calls → break
   f. For each tool_call:
      - Permission check (_check_permission)
      - If denied → yield PermissionRequest → user decides
      - Execute tool → yield ToolStart / ToolEnd
      - Append tool result
   g. Loop (model sees tool results and responds)
```

**Event types:**

| Event | Fields | When |
|---|---|---|
| `TextChunk` | `text` | Streaming text delta |
