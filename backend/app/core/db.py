"""Database engine and session helpers.

Metadata store is Postgres in production; the test suite uses SQLite (the schema is
kept dialect-portable — see ``app.models.base``).
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.core.config import get_settings

_engine: Engine | None = None


def make_engine(url: str | None = None) -> Engine:
    """Create a new engine for ``url`` (defaults to the configured DATABASE_URL)."""
    db_url = url or get_settings().database_url
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = make_engine()
    return _engine


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session bound to the process engine."""
    with Session(get_engine()) as session:
        yield session
