"""Reusable metric definition endpoints (see docs/06-api-and-sdk.md). Create requires editor+."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, TenantDep, require_min_role
from app.models.enums import MembershipRole
from app.schemas.metric import MetricCreate, MetricRead
from app.services import metrics as svc

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post(
    "",
    response_model=MetricRead,
    status_code=201,
    dependencies=[Depends(require_min_role(MembershipRole.editor))],
)
def create_metric(payload: MetricCreate, session: SessionDep, ctx: TenantDep) -> MetricRead:
    metric = svc.create_metric(session, ctx.org_id, ctx.workspace_id, payload)
    return MetricRead.model_validate(metric)


@router.get("", response_model=list[MetricRead])
def list_metrics(session: SessionDep, ctx: TenantDep) -> list[MetricRead]:
    return [MetricRead.model_validate(m) for m in svc.list_metrics(session, ctx.workspace_id)]
