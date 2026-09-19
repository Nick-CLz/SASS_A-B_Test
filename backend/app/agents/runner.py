"""Provider-neutral agent runner: drives a tool-use loop, records a full trace, and
persists it as AgentRun + AgentStep (the audit trail behind grounding).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlmodel import Session

from app.agents.grounding import ungrounded_numbers
from app.agents.model import ChatModel
from app.agents.tools import Tool, tool_schema
from app.models.agent import AgentRun, AgentStep
from app.models.enums import AgentRunStatus, AgentStepKind, AgentType
from app.services.repository import add


@dataclass
class Step:
    kind: str  # "message" | "tool_call" | "tool_result"
    tool_name: str | None
    input: dict[str, Any]
    output: dict[str, Any]


@dataclass
class AgentResult:
    text: str
    steps: list[Step] = field(default_factory=list)
    tool_outputs: list[dict[str, Any]] = field(default_factory=list)
    stopped: str = "complete"  # "complete" | "max_steps"

    @property
    def ungrounded(self) -> list[str]:
        """Numbers in the final text not traceable to a tool result (should be empty)."""
        return ungrounded_numbers(self.text, self.tool_outputs)


def run_agent(
    model: ChatModel, system: str, user: str, tools: list[Tool], *, max_steps: int = 8
) -> AgentResult:
    """Run the model + tools loop until the model answers (or the step cap is hit)."""
    registry = {tool.name: tool for tool in tools}
    schemas = [tool_schema(tool) for tool in tools]
    transcript: list[dict[str, Any]] = [{"role": "user", "text": user}]
    result = AgentResult(text="")

    for _ in range(max_steps):
        response = model.respond(system, transcript, schemas)
        if response.tool_calls:
            transcript.append(
                {"role": "assistant", "tool_calls": [vars(tc) for tc in response.tool_calls]}
            )
            for call in response.tool_calls:
                result.steps.append(Step("tool_call", call.name, call.input, {}))
                tool = registry.get(call.name)
                output = (
                    tool.run(call.input)
                    if tool is not None
                    else {"error": f"unknown tool: {call.name}"}
                )
                result.tool_outputs.append(output)
                result.steps.append(Step("tool_result", call.name, {}, output))
                transcript.append(
                    {"role": "tool", "tool_call_id": call.id, "name": call.name, "output": output}
                )
        else:
            result.text = response.text or ""
            result.steps.append(Step("message", None, {}, {"text": result.text}))
            return result

    result.stopped = "max_steps"
    return result


def persist_agent_run(
    session: Session,
    *,
    org_id: uuid.UUID,
    experiment_id: uuid.UUID | None,
    agent_type: AgentType,
    model_name: str,
    result: AgentResult,
) -> AgentRun:
    """Persist the run + every step (so each number is traceable to a tool result)."""
    run = AgentRun(
        org_id=org_id,
        experiment_id=experiment_id,
        agent_type=agent_type,
        model=model_name,
        status=AgentRunStatus.complete if result.stopped == "complete" else AgentRunStatus.failed,
    )
    add(session, run)
    for seq, step in enumerate(result.steps):
        session.add(
            AgentStep(
                org_id=org_id,
                agent_run_id=run.id,
                seq=seq,
                kind=AgentStepKind(step.kind),
                tool_name=step.tool_name,
                input=step.input,
                output=step.output,
            )
        )
    session.commit()
    session.refresh(run)
    return run
