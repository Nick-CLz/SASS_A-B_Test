"""Admin schemas: API keys and audit log (see docs/03-data-model.md)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=lambda: ["assign", "track"])


class ApiKeyRead(ORMModel):
    id: uuid.UUID
    name: str
    scopes: list[str]
    last_used_at: datetime | None


class ApiKeyCreated(ApiKeyRead):
    secret: str  # the plaintext key — shown only once, on creation


class AuditEntryRead(ORMModel):
    id: uuid.UUID
    action: str
    target_type: str
    target_id: uuid.UUID | None
    actor_kind: str
    created_at: datetime
    after: dict[str, Any] | None
