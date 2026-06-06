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
from app.analytics import DuckStore
from app.api.deps import get_store
from app.core.config import get_settings
from app.core.db import get_session, make_engine
from app.main import app
from app.models import Organization, Workspace
from fastapi.testclient import TestClient
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


@pytest.fixture
def store() -> Iterator[DuckStore]:
    """An isolated in-memory analytics store for a test."""
    duck = DuckStore(":memory:")
    try:
        yield duck
    finally:
        duck.close()


@pytest.fixture
def client(migrated_engine: Engine, store: DuckStore) -> Iterator[TestClient]:
    """A TestClient bound to the migrated DB and the in-memory analytics store."""

    def _override_session() -> Iterator[Session]:
        with Session(migrated_engine) as test_session:
            yield test_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def tenant(migrated_engine: Engine) -> dict[str, str]:
    """Create an org + workspace; return their ids (workspace_id is the X-Workspace-Id)."""
    with Session(migrated_engine) as setup_session:
        org = Organization(name="Acme", slug="acme")
        setup_session.add(org)
        setup_session.commit()
        setup_session.refresh(org)
        workspace = Workspace(org_id=org.id, name="Web", slug="web")
        setup_session.add(workspace)
        setup_session.commit()
        setup_session.refresh(workspace)
        return {"org_id": str(org.id), "workspace_id": str(workspace.id)}
