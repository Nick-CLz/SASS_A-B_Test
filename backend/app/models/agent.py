"""Agent execution trace: runs and steps (the audit trail behind grounding)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import ConfigDict
from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import Base, enum_type, json_type
from app.models.enums import AgentRunStatus, AgentStepKind, AgentType


class AgentRun(Base, table=True):
    __tablename__ = "agent_run"
    # 'model' would otherwise collide with pydantic's protected 'model_' namespace.
    model_config = ConfigDict(protected_namespaces=())  # type: ignore[assignment]

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    experiment_id: uuid.UUID | None = Field(default=None, foreign_key="experiment.id")
    agent_type: AgentType = Field(sa_type=enum_type(AgentType))
    model: str = ""
    status: AgentRunStatus = Field(
        default=AgentRunStatus.pending, sa_type=enum_type(AgentRunStatus)
    )
    cost_tokens: int = 0
    latency_ms: int | None = None


class AgentStep(Base, table=True):
    __tablename__ = "agent_step"
    __table_args__ = (UniqueConstraint("agent_run_id", "seq", name="uq_agentstep_run_seq"),)

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    agent_run_id: uuid.UUID = Field(foreign_key="agent_run.id", index=True)
    seq: int
    kind: AgentStepKind = Field(sa_type=enum_type(AgentStepKind))
    tool_name: str | None = None
    input: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    output: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
