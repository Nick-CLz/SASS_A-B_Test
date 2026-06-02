"""Shared model base: UUIDv7 primary keys, timestamps, and column-type helpers.

See ``docs/03-data-model.md``. Kept dialect-portable: JSON columns become JSONB on
Postgres and plain JSON elsewhere (e.g. the SQLite test database); Python enums are
stored as checked VARCHARs (no native Postgres enum types → simpler migrations).
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def uuid7() -> uuid.UUID:
    """Generate a UUIDv7 (time-ordered, sortable) identifier."""
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = int.from_bytes(os.urandom(2), "big") & ((1 << 12) - 1)
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    value = (ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return uuid.UUID(int=value)


def utcnow() -> datetime:
    """Timezone-aware current UTC timestamp."""
    return datetime.now(UTC)


def json_type() -> Any:
    """JSON column type: JSONB on Postgres, JSON elsewhere."""
    return JSON().with_variant(JSONB(), "postgresql")


def enum_type(enum_cls: type[Enum]) -> Any:
    """Store a Python Enum as a checked VARCHAR (non-native → migration-friendly)."""
    return SAEnum(enum_cls, native_enum=False)


class Base(SQLModel):
    """Common columns for every table: UUIDv7 PK + created/updated timestamps."""

    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": utcnow},
    )
