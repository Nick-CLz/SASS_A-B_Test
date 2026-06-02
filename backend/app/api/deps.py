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

from app.core.db import get_session
from app.core.errors import NotFoundError
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
