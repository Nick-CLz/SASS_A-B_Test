"""Admin endpoints: API keys + audit log (admin role required)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, TenantDep, require_min_role
from app.models.enums import MembershipRole
from app.schemas.admin import ApiKeyCreate, ApiKeyCreated, ApiKeyRead, AuditEntryRead
from app.schemas.usage import UsageRead
from app.services import api_keys as keys_svc
from app.services import audit as audit_svc
from app.services import usage as usage_svc

router = APIRouter(tags=["admin"])

_admin = Depends(require_min_role(MembershipRole.admin))


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=201, dependencies=[_admin])
def create_api_key(payload: ApiKeyCreate, session: SessionDep, ctx: TenantDep) -> ApiKeyCreated:
    key, secret = keys_svc.create_api_key(session, ctx.org_id, payload.name, payload.scopes)
    return ApiKeyCreated(
        id=key.id,
        name=key.name,
        scopes=key.scopes,
        last_used_at=key.last_used_at,
        secret=secret,
    )


@router.get("/api-keys", response_model=list[ApiKeyRead], dependencies=[_admin])
def list_api_keys(session: SessionDep, ctx: TenantDep) -> list[ApiKeyRead]:
    return [ApiKeyRead.model_validate(k) for k in keys_svc.list_api_keys(session, ctx.org_id)]


@router.get("/audit", response_model=list[AuditEntryRead], dependencies=[_admin])
def list_audit(session: SessionDep, ctx: TenantDep) -> list[AuditEntryRead]:
    return [AuditEntryRead.model_validate(e) for e in audit_svc.list_audit(session, ctx.org_id)]


@router.get("/usage", response_model=UsageRead, dependencies=[_admin])
def usage(
    session: SessionDep,
    ctx: TenantDep,
    since: datetime | None = None,
    until: datetime | None = None,
) -> UsageRead:
    summary = usage_svc.usage_summary(session, ctx.org_id, since=since, until=until)
    return UsageRead(
        org_id=summary.org_id,
        period_start=summary.period_start,
        period_end=summary.period_end,
        agent_runs=summary.agent_runs,
        agent_cost_tokens=summary.agent_cost_tokens,
        analyses=summary.analyses,
        agent_runs_by_type=summary.agent_runs_by_type,
    )
