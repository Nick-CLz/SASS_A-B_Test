"""Assignment request/response schemas (see docs/06-api-and-sdk.md)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AssignRequest(BaseModel):
    unit_id: str
    experiment_key: str | None = None  # omit to evaluate all running experiments
    attributes: dict[str, Any] = Field(default_factory=dict)


class AssignmentRead(ORMModel):
    experiment_key: str
    eligible: bool
    in_experiment: bool
    variant_key: str | None
    reason: str


class AssignResponse(BaseModel):
    assignments: list[AssignmentRead]
