"""Grounded AI agent layer (P11 foundation; agents in P12-P14).

Agents act only through typed tools that call the deterministic engine, and every number
they report must trace to a tool result (see ``grounding``). The runner is provider-neutral;
a ``MockModel`` makes everything testable without an API key. See docs/05-ai-agents.md.
"""

from app.agents.grounding import ungrounded_numbers
from app.agents.model import (
    AnthropicModel,
    ChatModel,
    MockModel,
    ModelResponse,
    ToolCall,
    get_live_model,
)
from app.agents.runner import AgentResult, Step, persist_agent_run, run_agent
from app.agents.tools import Tool, tool_schema

__all__ = [
    "AgentResult",
    "AnthropicModel",
    "ChatModel",
    "MockModel",
    "ModelResponse",
    "Step",
    "Tool",
    "ToolCall",
    "get_live_model",
    "persist_agent_run",
    "run_agent",
    "tool_schema",
    "ungrounded_numbers",
]
