"""Shared test fixtures.

Tests run against a throwaway SQLite database that has the Alembic migration applied
(Postgres isn't available in CI/sandbox; the schema is dialect-portable — see
``app.models.base``).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.core.db import make_engine
from sqlalchemy.engine import Engine
from sqlmodel import Session


@pytest.fixture
def db_url(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """A temp SQLite URL, exported as DATABASE_URL so Alembic env.py picks it up."""
    url = f"sqlite:///{tmp_path}/test.db"  # type: ignore[operator]
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    yield url
    get_settings.cache_clear()


@pytest.fixture
def migrated_engine(db_url: str) -> Iterator[Engine]:
    """An engine bound to a database with ``alembic upgrade head`` applied."""
    command.upgrade(Config("alembic.ini"), "head")
    engine = make_engine(db_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session(migrated_engine: Engine) -> Iterator[Session]:
    """A session on the migrated database."""
    with Session(migrated_engine) as session:
        yield session
