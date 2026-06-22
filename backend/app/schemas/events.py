"""Ingestion request/response schemas (POST /v1/events)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    unit_id: str
    name: str
    ts: datetime | None = None
    value: float | None = None
    props: dict[str, Any] = Field(default_factory=dict)
    event_id: str | None = None  # client-supplied id → idempotent ingestion


class ExposureIn(BaseModel):
    experiment_key: str
    variant_key: str
    unit_id: str
    ts: datetime | None = None
    attrs: dict[str, Any] = Field(default_factory=dict)


class EventsRequest(BaseModel):
    events: list[EventIn] = Field(default_factory=list)
    exposures: list[ExposureIn] = Field(default_factory=list)


class RejectedItem(BaseModel):
    index: int
    kind: str  # "event" | "exposure"
    reason: str


class EventsResponse(BaseModel):
    accepted: int
    rejected: list[RejectedItem] = Field(default_factory=list)
