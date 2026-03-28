"""Tests for compaction.py — token estimation, context limits, snipping, split point."""
from __future__ import annotations

import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from compaction import estimate_tokens, get_context_limit, snip_old_tool_results, find_split_point


# ── estimate_tokens ───────────────────────────────────────────────────────

class TestEstimateTokens:
    def test_simple_messages(self):
        msgs = [
            {"role": "user", "content": "Hello world"},          # 11 chars
            {"role": "assistant", "content": "Hi there!"},       # 9 chars
        ]
        result = estimate_tokens(msgs)
        # (11 + 9) / 3.5 = 5.71 -> 5
        assert result == int(20 / 3.5)

    def test_empty_messages(self):
        assert estimate_tokens([]) == 0

    def test_empty_content(self):
        msgs = [{"role": "user", "content": ""}]
        assert estimate_tokens(msgs) == 0

    def test_tool_result_messages(self):
        msgs = [
            {"role": "tool", "tool_call_id": "abc", "name": "Read", "content": "x" * 350},
        ]
        result = estimate_tokens(msgs)
        assert result == int(350 / 3.5)

    def test_structured_content(self):
        """Content that is a list of dicts (e.g. Anthropic tool_result blocks)."""
        msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "id1", "content": "A" * 70},
                ],
            },
        ]
        result = estimate_tokens(msgs)
        # "tool_result" (11) + "id1" (3) + "A"*70 (70) = 84  -> 84/3.5 = 24
        assert result == int(84 / 3.5)

    def test_with_tool_calls(self):
        msgs = [
            {
                "role": "assistant",
                "content": "ok",
                "tool_calls": [
                    {"id": "c1", "name": "Bash", "input": {"command": "ls"}},
                ],
            },
        ]
        result = estimate_tokens(msgs)
        # content "ok" (2) + tool_calls string values: "c1" (2) + "Bash" (4) = 8
        assert result == int(8 / 3.5)


# ── get_context_limit ─────────────────────────────────────────────────────

class TestGetContextLimit:
    def test_anthropic(self):
        assert get_context_limit("claude-opus-4-6") == 200000

    def test_gemini(self):
        assert get_context_limit("gemini-2.0-flash") == 1000000

    def test_deepseek(self):
        assert get_context_limit("deepseek-chat") == 64000

    def test_openai(self):
        assert get_context_limit("gpt-4o") == 128000

    def test_qwen(self):
        assert get_context_limit("qwen-max") == 1000000
