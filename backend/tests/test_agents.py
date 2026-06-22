"""Agent foundation: tool-use loop, grounding (no invented numbers), and trace persistence.

All deterministic via a MockModel — no API key required.
"""

from __future__ import annotations

from app.agents.model import MockModel, ModelResponse, ToolCall
from app.agents.runner import persist_agent_run, run_agent
from app.agents.tools import Tool
from app.models import AgentStep, Organization
from app.models.enums import AgentType
from app.services.repository import add
from sqlmodel import Session, select


def _rate_tool() -> Tool:
    return Tool(
        name="get_rate",
        description="Return the conversion rate.",
        parameters={"type": "object", "properties": {}},
        handler=lambda _args: {"rate": 0.14},
    )


def test_run_agent_calls_tool_then_answers() -> None:
    model = MockModel(
        [
            ModelResponse(tool_calls=[ToolCall(id="1", name="get_rate", input={})]),
            ModelResponse(text="The conversion rate is 0.14."),
        ]
    )
    result = run_agent(model, "system", "what is the rate?", [_rate_tool()])
    assert result.text == "The conversion rate is 0.14."
    assert {"rate": 0.14} in result.tool_outputs
    assert result.ungrounded == []  # 0.14 came from the tool


def test_grounding_flags_an_invented_number() -> None:
    model = MockModel(
        [
            ModelResponse(tool_calls=[ToolCall(id="1", name="get_rate", input={})]),
            ModelResponse(text="The rate is 0.99."),  # not from any tool result
        ]
    )
    result = run_agent(model, "s", "u", [_rate_tool()])
    assert result.ungrounded == ["0.99"]


def test_unknown_tool_is_handled_gracefully() -> None:
    model = MockModel(
        [
            ModelResponse(tool_calls=[ToolCall(id="1", name="missing", input={})]),
            ModelResponse(text="done"),
        ]
    )
    result = run_agent(model, "s", "u", [_rate_tool()])
    assert any("error" in output for output in result.tool_outputs)


def test_step_cap_is_enforced() -> None:
    looping = MockModel(
        [ModelResponse(tool_calls=[ToolCall(id="1", name="get_rate", input={})])] * 10
    )
    result = run_agent(looping, "s", "u", [_rate_tool()], max_steps=3)
    assert result.stopped == "max_steps"


def test_persist_agent_run_writes_full_trace(session: Session) -> None:
    org = add(session, Organization(name="Acme", slug="acme"))
    model = MockModel(
        [
            ModelResponse(tool_calls=[ToolCall(id="1", name="get_rate", input={})]),
            ModelResponse(text="rate 0.14"),
        ]
    )
    result = run_agent(model, "s", "u", [_rate_tool()])
    run = persist_agent_run(
        session,
        org_id=org.id,
        experiment_id=None,
        agent_type=AgentType.analyst,
        model_name="mock",
        result=result,
    )
    steps = session.exec(select(AgentStep).where(AgentStep.agent_run_id == run.id)).all()
    assert len(steps) == len(result.steps)
    assert run.status.value == "complete"
