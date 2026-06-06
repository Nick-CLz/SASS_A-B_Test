"""FastAPI dependencies: DB session + (stubbed) tenant context.

Real authentication / RBAC arrives in P15. For now the tenant is resolved from the
``X-Workspace-Id`` header and the caller is treated as an owner, so handlers can already
be written tenant-scoped (they filter by ``ctx.workspace_id`` / ``ctx.org_id``).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header
from pydantic import BaseModel
from sqlmodel import Session

from app.analytics import DuckStore, get_store_singleton
from app.assignment.exposure import ExposureSink
from app.core.db import get_session
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.ingestion.sink import DuckExposureSink
from app.models.enums import MembershipRole
from app.models.org import Workspace
from app.services.api_keys import verify_key

SessionDep = Annotated[Session, Depends(get_session)]


class TenantContext(BaseModel):
    """The resolved tenant for a request."""

    org_id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None = None
    role: MembershipRole = MembershipRole.owner


def _scope_to_role(scopes: list[str]) -> MembershipRole:
    return MembershipRole.admin if "admin" in scopes else MembershipRole.editor


def get_tenant(
    session: SessionDep,
    x_workspace_id: Annotated[uuid.UUID, Header()],
    x_role: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
) -> TenantContext:
    """Resolve the tenant from headers.

    Auth is pluggable (a real provider lands later): an ``X-Api-Key`` is verified and its
    scopes map to a role; otherwise an ``X-Role`` header selects the role (default owner)
    for local/dev use. The workspace must belong to the principal's org.
    """
    workspace = session.get(Workspace, x_workspace_id)
    if workspace is None:
        raise NotFoundError(f"workspace {x_workspace_id} not found")
    role = MembershipRole.owner
    if x_api_key is not None:
        key = verify_key(session, x_api_key)
        if key is None or key.org_id != workspace.org_id:
            raise UnauthorizedError("invalid API key for this workspace")
        role = _scope_to_role(key.scopes)
    elif x_role is not None:
        try:
            role = MembershipRole(x_role)
        except ValueError as exc:
            raise ForbiddenError(f"unknown role: {x_role}") from exc
    return TenantContext(org_id=workspace.org_id, workspace_id=workspace.id, role=role)


TenantDep = Annotated[TenantContext, Depends(get_tenant)]

ROLE_RANK: dict[MembershipRole, int] = {
    MembershipRole.viewer: 0,
    MembershipRole.analyst: 1,
    MembershipRole.editor: 2,
    MembershipRole.admin: 3,
    MembershipRole.owner: 4,
}


def require_min_role(minimum: MembershipRole) -> Callable[[TenantContext], None]:
    """Dependency factory: raises 403 unless the caller's role meets ``minimum``."""

    def checker(ctx: TenantDep) -> None:
        if ROLE_RANK[ctx.role] < ROLE_RANK[minimum]:
            raise ForbiddenError(f"action requires '{minimum.value}' role or higher")

    return checker


def get_store() -> DuckStore:
    """The analytics store (DuckDB). Overridden in tests with an in-memory store."""
    return get_store_singleton()


StoreDep = Annotated[DuckStore, Depends(get_store)]


def get_exposure_sink(store: StoreDep) -> ExposureSink:
    """Persist assignment exposures to the analytics store (P04 → P06 wiring)."""
    return DuckExposureSink(store)


ExposureSinkDep = Annotated[ExposureSink, Depends(get_exposure_sink)]
