"""Experiment / variant / metric-attachment request & response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import (
    ExperimentDecision,
    ExperimentMetricRole,
    ExperimentStatus,
    RandomizationUnit,
)
from app.schemas.common import ORMModel


class VariantCreate(BaseModel):
    key: str
    name: str = ""
    is_control: bool = False
    allocation_pct: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)


class VariantRead(ORMModel):
    id: uuid.UUID
    key: str
    name: str
    is_control: bool
    allocation_pct: float
    payload: dict[str, Any]


class ExperimentMetricAttach(BaseModel):
    metric_id: uuid.UUID
    role: ExperimentMetricRole = ExperimentMetricRole.secondary
    min_detectable_effect: float | None = None
    is_oec: bool = False


class ExperimentMetricRead(ORMModel):
    id: uuid.UUID
    metric_id: uuid.UUID
    role: ExperimentMetricRole
    min_detectable_effect: float | None
    is_oec: bool


class ExperimentCreate(BaseModel):
    key: str
    name: str
    description: str = ""
    hypothesis: str = ""
    randomization_unit: RandomizationUnit = RandomizationUnit.user_id
    layer_id: uuid.UUID | None = None
    allocation: dict[str, Any] = Field(default_factory=dict)
    targeting: dict[str, Any] = Field(default_factory=dict)
    salt: str = ""
    variants: list[VariantCreate] = Field(default_factory=list)


class ExperimentUpdate(BaseModel):
    """All fields optional; only provided fields are changed (draft/review only)."""

    name: str | None = None
    description: str | None = None
    hypothesis: str | None = None
    randomization_unit: RandomizationUnit | None = None
    layer_id: uuid.UUID | None = None
    allocation: dict[str, Any] | None = None
    targeting: dict[str, Any] | None = None


class ExperimentTransition(BaseModel):
    status: ExperimentStatus


class ExperimentRead(ORMModel):
    id: uuid.UUID
    key: str
    name: str
    description: str
    hypothesis: str
    status: ExperimentStatus
    randomization_unit: RandomizationUnit
    layer_id: uuid.UUID | None
    allocation: dict[str, Any]
    targeting: dict[str, Any]
    salt: str
    decision: ExperimentDecision | None
    start_at: datetime | None
    end_at: datetime | None
    variants: list[VariantRead] = Field(default_factory=list)
    metrics: list[ExperimentMetricRead] = Field(default_factory=list)
