"""Tool framework: agents act only through typed tools that wrap existing engine code.

A tool's handler is a plain Python callable (no LLM), so it is unit-tested on its own and
the agent's behaviour is separable from tool correctness (see docs/05-ai-agents.md).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the tool input
    handler: Callable[[dict[str, Any]], dict[str, Any]]

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.handler(args)


def tool_schema(tool: Tool) -> dict[str, Any]:
    """Render a tool in the Anthropic tool-use schema."""
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters,
    }
