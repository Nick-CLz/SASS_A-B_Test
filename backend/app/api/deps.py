"""FastAPI dependencies: DB session + tenant context (auth + RBAC).

The tenant is resolved from ``X-Workspace-Id`` plus one of: an ``X-Api-Key`` (scopes -> role),
an SSO ``Authorization: Bearer <JWT>`` (claims -> role), or an ``X-Role`` header for local/dev
(default owner). The workspace must belong to the principal's org. See docs/03-data-model.md.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header
from pydantic import BaseModel
from sqlmodel import Session

from app.analytics import AnalyticsBackend, get_store_singleton
from app.assignment.exposure import ExposureSink
from app.core.config import get_settings
from app.core.db import get_session
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.jwt import decode_hs256
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


def _claim_role(value: object) -> MembershipRole:
    """Map an SSO token's ``role`` claim to a role (unknown -> least privilege)."""
    try:
        return MembershipRole(str(value))
    except ValueError:
        return MembershipRole.viewer


def get_tenant(
    session: SessionDep,
    x_workspace_id: Annotated[uuid.UUID, Header()],
    x_role: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> TenantContext:
    """Resolve the tenant from headers: X-Api-Key, then SSO bearer JWT, then X-Role (dev)."""
    workspace = session.get(Workspace, x_workspace_id)
    if workspace is None:
        raise NotFoundError(f"workspace {x_workspace_id} not found")

    settings = get_settings()
    role = MembershipRole.owner
    user_id: uuid.UUID | None = None

    if x_api_key is not None:
        key = verify_key(session, x_api_key)
        if key is None or key.org_id != workspace.org_id:
            raise UnauthorizedError("invalid API key for this workspace")
        role = _scope_to_role(key.scopes)
    elif (
        authorization is not None
        and authorization.lower().startswith("bearer ")
        and settings.sso_jwt_secret is not None
    ):
        claims = decode_hs256(
            authorization[7:].strip(),
            settings.sso_jwt_secret,
            audience=settings.sso_jwt_audience,
        )
        claim_org = claims.get("org")
        if claim_org is not None and str(claim_org) != str(workspace.org_id):
            raise UnauthorizedError("token org does not match workspace")
        role = _claim_role(claims.get("role"))
        sub = claims.get("sub")
        if isinstance(sub, str):
            try:
                user_id = uuid.UUID(sub)
            except ValueError:
                user_id = None
    elif x_role is not None:
        try:
            role = MembershipRole(x_role)
        except ValueError as exc:
            raise ForbiddenError(f"unknown role: {x_role}") from exc

    return TenantContext(
        org_id=workspace.org_id, workspace_id=workspace.id, role=role, user_id=user_id
    )


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


def get_store() -> AnalyticsBackend:
    """The analytics backend (DuckDB by default). Overridden in tests with an in-memory store."""
    return get_store_singleton()


StoreDep = Annotated[AnalyticsBackend, Depends(get_store)]


def get_exposure_sink(store: StoreDep) -> ExposureSink:
    """Persist assignment exposures to the analytics store (P04 → P06 wiring)."""
    return DuckExposureSink(store)


ExposureSinkDep = Annotated[ExposureSink, Depends(get_exposure_sink)]
