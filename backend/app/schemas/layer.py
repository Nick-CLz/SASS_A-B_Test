"""Layer (mutual-exclusion group / holdout) request & response schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class LayerCreate(BaseModel):
    name: str
    traffic_partitions: dict[str, Any] = Field(default_factory=dict)


class LayerRead(ORMModel):
    id: uuid.UUID
    name: str
    traffic_partitions: dict[str, Any]
