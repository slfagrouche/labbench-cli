"""Memory context building for system prompt injection.

Provides:
  get_memory_context()      — full context string for system prompt
  find_relevant_memories()  — keyword (+ optional AI) relevance filtering
  truncate_index_content()  — line + byte truncation with warning
"""
from __future__ import annotations

from pathlib import Path

from .store import (
    USER_MEMORY_DIR,
    INDEX_FILENAME,
    MAX_INDEX_LINES,
    MAX_INDEX_BYTES,
    get_memory_dir,
    get_index_content,
    load_entries,
    search_memory,
)
from .scan import scan_all_memories, format_memory_manifest, memory_freshness_text
from .types import MEMORY_SYSTEM_PROMPT


# ── Index truncation ───────────────────────────────────────────────────────

def truncate_index_content(raw: str) -> str:
    """Truncate MEMORY.md content to line AND byte limits, appending a warning.

    Truncates very large files when injecting context:
      - Line-truncates first (natural boundary)
      - Then byte-truncates at the last newline before the cap
      - Appends which limit fired
    """
    trimmed = raw.strip()
    content_lines = trimmed.split("\n")
    line_count = len(content_lines)
    byte_count = len(trimmed.encode())

    was_line_truncated = line_count > MAX_INDEX_LINES
    was_byte_truncated = byte_count > MAX_INDEX_BYTES

    if not was_line_truncated and not was_byte_truncated:
        return trimmed

    truncated = "\n".join(content_lines[:MAX_INDEX_LINES]) if was_line_truncated else trimmed

    if len(truncated.encode()) > MAX_INDEX_BYTES:
        # Cut at last newline before byte limit
        raw_bytes = truncated.encode()
        cut = raw_bytes[:MAX_INDEX_BYTES].rfind(b"\n")
        truncated = raw_bytes[: cut if cut > 0 else MAX_INDEX_BYTES].decode(errors="replace")

    if was_byte_truncated and not was_line_truncated:
        reason = f"{byte_count:,} bytes (limit: {MAX_INDEX_BYTES:,}) — index entries are too long"
    elif was_line_truncated and not was_byte_truncated:
        reason = f"{line_count} lines (limit: {MAX_INDEX_LINES})"
    else:
        reason = f"{line_count} lines and {byte_count:,} bytes"

    warning = (
        f"\n\n> WARNING: {INDEX_FILENAME} is {reason}. "
        "Only part of it was loaded. Keep index entries to one line under ~150 chars."
    )
    return truncated + warning


# ── System prompt context ──────────────────────────────────────────────────

def get_memory_context(include_guidance: bool = False) -> str:
    """Return memory context for injection into the system prompt.

    Combines user-level and project-level MEMORY.md content (if present).
    Returns empty string when no memories exist.

    Args:
        include_guidance: if True, prepend the full memory system guidance
                          (MEMORY_SYSTEM_PROMPT). Normally False since the
                          system prompt template already includes brief guidance.
    """
    parts: list[str] = []

    # User-level index
    user_content = get_index_content("user")
    if user_content:
        truncated = truncate_index_content(user_content)
        parts.append(truncated)

    # Project-level index (labelled separately)
    proj_content = get_index_content("project")
    if proj_content:
        truncated = truncate_index_content(proj_content)
        parts.append(f"[Project memories]\n{truncated}")

    if not parts:
        return ""

    body = "\n\n".join(parts)
