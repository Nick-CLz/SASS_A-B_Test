"""Usage metering response schema (GET /v1/usage)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UsageRead(BaseModel):
    org_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    agent_runs: int
    agent_cost_tokens: int
    analyses: int
    agent_runs_by_type: dict[str, int] = Field(default_factory=dict)
