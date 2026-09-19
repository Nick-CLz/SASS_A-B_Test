"""Grounding check: an agent may only report numbers it obtained from tool results.

This is the guarantee that makes the AI layer trustworthy (docs/05-ai-agents.md): no
LLM-invented statistics. ``ungrounded_numbers`` returns any number in the agent's text that
does not trace to a tool output (allowing rounded prefixes, e.g. 0.14 from 0.142857).
"""

from __future__ import annotations

import json
import re

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _numbers_in(obj: object) -> set[str]:
    return set(_NUMBER.findall(json.dumps(obj, default=str)))


def ungrounded_numbers(text: str, tool_outputs: list[dict[str, object]]) -> list[str]:
    """Numbers in ``text`` that do not appear in any tool output."""
    sourced: set[str] = set()
    for output in tool_outputs:
        sourced |= _numbers_in(output)
    flagged: list[str] = []
    for number in _NUMBER.findall(text):
        if any(number == s or number in s or s in number for s in sourced):
            continue
        flagged.append(number)
    return flagged
