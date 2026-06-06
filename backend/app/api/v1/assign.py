"""Assignment endpoint: POST /v1/assign (see docs/06-api-and-sdk.md)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ExposureSinkDep, SessionDep, TenantDep
from app.schemas.assign import AssignmentRead, AssignRequest, AssignResponse
from app.services import assignment as svc

router = APIRouter(tags=["assignment"])


@router.post("/assign", response_model=AssignResponse)
def assign_unit(
    payload: AssignRequest, session: SessionDep, ctx: TenantDep, sink: ExposureSinkDep
) -> AssignResponse:
    results = svc.assign_unit(
        session,
        ctx.workspace_id,
        payload.unit_id,
        payload.attributes,
        payload.experiment_key,
        sink=sink,
    )
    return AssignResponse(assignments=[AssignmentRead.model_validate(result) for result in results])
