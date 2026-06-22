"""Pluggable chat model for the agent layer.

A ``MockModel`` (scripted) makes the agents fully testable with no API key; an
``AnthropicModel`` is used for live runs when ``ANTHROPIC_API_KEY`` is set. The runner
is provider-neutral — it speaks ``ModelResponse`` (text or tool calls), not a vendor format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from app.core.config import get_settings


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ModelResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ChatModel(Protocol):
    def respond(
        self, system: str, transcript: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse: ...


class MockModel:
    """Replays a scripted list of responses (deterministic tests, no network)."""

    def __init__(self, script: list[ModelResponse]) -> None:
        self._script = list(script)
        self._index = 0

    def respond(
        self, system: str, transcript: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse:
        if self._index >= len(self._script):
            return ModelResponse(text="(no more scripted responses)")
        response = self._script[self._index]
        self._index += 1
        return response


def _to_anthropic_messages(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in transcript:
        role = entry["role"]
        if role == "user":
            messages.append({"role": "user", "content": entry["text"]})
        elif role == "assistant":
            messages.append(
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc["input"],
                        }
                        for tc in entry["tool_calls"]
                    ],
                }
            )
        elif role == "tool":
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": entry["tool_call_id"],
                            "content": str(entry["output"]),
                        }
                    ],
                }
            )
    return messages


class AnthropicModel:
    """Live model via the Anthropic SDK (used only when an API key is configured)."""

    def __init__(self, model: str, api_key: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def respond(
        self, system: str, transcript: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelResponse:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            tools=cast(Any, tools),
            messages=cast(Any, _to_anthropic_messages(transcript)),
        )
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, input=dict(block.input)))
        return ModelResponse(text="".join(text_parts) or None, tool_calls=calls)


def get_live_model(tier: str = "medium") -> AnthropicModel:
    """Construct the configured Anthropic model for ``tier`` (small|medium|large)."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; agents cannot run live")
    model = {
        "small": settings.agent_model_small,
        "medium": settings.agent_model_medium,
        "large": settings.agent_model_large,
    }.get(tier, settings.agent_model_medium)
    return AnthropicModel(model, settings.anthropic_api_key)
