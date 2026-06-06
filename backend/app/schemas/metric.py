"""Metric definition request & response schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import MetricDirection, MetricType
from app.schemas.common import ORMModel


class MetricCreate(BaseModel):
    key: str
    name: str
    type: MetricType
    numerator: dict[str, Any] = Field(default_factory=dict)
    denominator: dict[str, Any] | None = None
    direction: MetricDirection = MetricDirection.increase_good
    unit: str | None = None
    winsorize_pct: float | None = None


class MetricRead(ORMModel):
    id: uuid.UUID
    key: str
    name: str
    type: MetricType
    numerator: dict[str, Any]
    denominator: dict[str, Any] | None
    direction: MetricDirection
    unit: str | None
    winsorize_pct: float | None
