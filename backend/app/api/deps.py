"""FastAPI dependencies: DB session + (stubbed) tenant context.

Real authentication / RBAC arrives in P15. For now the tenant is resolved from the
``X-Workspace-Id`` header and the caller is treated as an owner, so handlers can already
be written tenant-scoped (they filter by ``ctx.workspace_id`` / ``ctx.org_id``).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header
from pydantic import BaseModel
from sqlmodel import Session

from app.analytics import DuckStore, get_store_singleton
from app.assignment.exposure import ExposureSink
from app.core.db import get_session
from app.core.errors import NotFoundError
from app.ingestion.sink import DuckExposureSink
from app.models.enums import MembershipRole
from app.models.org import Workspace

SessionDep = Annotated[Session, Depends(get_session)]


class TenantContext(BaseModel):
    """The resolved tenant for a request."""

    org_id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None = None
    role: MembershipRole = MembershipRole.owner


def get_tenant(
    session: SessionDep,
    x_workspace_id: Annotated[uuid.UUID, Header()],
) -> TenantContext:
    """Resolve the workspace (and its org) from the ``X-Workspace-Id`` header."""
    workspace = session.get(Workspace, x_workspace_id)
    if workspace is None:
        raise NotFoundError(f"workspace {x_workspace_id} not found")
    return TenantContext(org_id=workspace.org_id, workspace_id=workspace.id)


TenantDep = Annotated[TenantContext, Depends(get_tenant)]


def get_store() -> DuckStore:
    """The analytics store (DuckDB). Overridden in tests with an in-memory store."""
    return get_store_singleton()


StoreDep = Annotated[DuckStore, Depends(get_store)]


def get_exposure_sink(store: StoreDep) -> ExposureSink:
    """Persist assignment exposures to the analytics store (P04 → P06 wiring)."""
    return DuckExposureSink(store)


ExposureSinkDep = Annotated[ExposureSink, Depends(get_exposure_sink)]
