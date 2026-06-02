"""Layer (mutual-exclusion / holdout) endpoints (see docs/06-api-and-sdk.md)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SessionDep, TenantDep
from app.schemas.layer import LayerCreate, LayerRead
from app.services import layers as svc

router = APIRouter(prefix="/layers", tags=["layers"])


@router.post("", response_model=LayerRead, status_code=201)
def create_layer(payload: LayerCreate, session: SessionDep, ctx: TenantDep) -> LayerRead:
    layer = svc.create_layer(session, ctx.org_id, ctx.workspace_id, payload)
    return LayerRead.model_validate(layer)


@router.get("", response_model=list[LayerRead])
def list_layers(session: SessionDep, ctx: TenantDep) -> list[LayerRead]:
    return [LayerRead.model_validate(layer) for layer in svc.list_layers(session, ctx.workspace_id)]
