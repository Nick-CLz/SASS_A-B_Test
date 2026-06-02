"""Experiment CRUD + lifecycle endpoints (see docs/06-api-and-sdk.md)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import Session

from app.api.deps import SessionDep, TenantDep
from app.models.enums import ExperimentStatus
from app.models.experiment import Experiment
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentMetricAttach,
    ExperimentMetricRead,
    ExperimentRead,
    ExperimentTransition,
    ExperimentUpdate,
    VariantCreate,
    VariantRead,
)
from app.services import experiments as svc

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _to_read(session: Session, exp: Experiment) -> ExperimentRead:
    read = ExperimentRead.model_validate(exp)
    read.variants = [VariantRead.model_validate(v) for v in svc.get_variants(session, exp.id)]
    read.metrics = [
        ExperimentMetricRead.model_validate(m) for m in svc.get_experiment_metrics(session, exp.id)
    ]
    return read


@router.post("", response_model=ExperimentRead, status_code=201)
def create_experiment(
    payload: ExperimentCreate, session: SessionDep, ctx: TenantDep
) -> ExperimentRead:
    exp = svc.create_experiment(session, ctx.org_id, ctx.workspace_id, payload)
    return _to_read(session, exp)


@router.get("", response_model=list[ExperimentRead])
def list_experiments(
    session: SessionDep, ctx: TenantDep, status: ExperimentStatus | None = None
) -> list[ExperimentRead]:
    return [_to_read(session, e) for e in svc.list_experiments(session, ctx.workspace_id, status)]


@router.get("/{key}", response_model=ExperimentRead)
def get_experiment(key: str, session: SessionDep, ctx: TenantDep) -> ExperimentRead:
    return _to_read(session, svc.get_experiment(session, ctx.workspace_id, key))


@router.patch("/{key}", response_model=ExperimentRead)
def update_experiment(
    key: str, payload: ExperimentUpdate, session: SessionDep, ctx: TenantDep
) -> ExperimentRead:
    return _to_read(session, svc.update_experiment(session, ctx.workspace_id, key, payload))


@router.post("/{key}/transition", response_model=ExperimentRead)
def transition_experiment(
    key: str, payload: ExperimentTransition, session: SessionDep, ctx: TenantDep
) -> ExperimentRead:
    exp = svc.transition_experiment(session, ctx.workspace_id, key, payload.status)
    return _to_read(session, exp)


@router.post("/{key}/variants", response_model=VariantRead, status_code=201)
def add_variant(
    key: str, payload: VariantCreate, session: SessionDep, ctx: TenantDep
) -> VariantRead:
    variant = svc.add_variant(session, ctx.org_id, ctx.workspace_id, key, payload)
    return VariantRead.model_validate(variant)


@router.post("/{key}/metrics", response_model=ExperimentMetricRead, status_code=201)
def attach_metric(
    key: str, payload: ExperimentMetricAttach, session: SessionDep, ctx: TenantDep
) -> ExperimentMetricRead:
    link = svc.attach_metric(session, ctx.org_id, ctx.workspace_id, key, payload)
    return ExperimentMetricRead.model_validate(link)
