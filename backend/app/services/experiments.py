"""Experiment service: invariants, lifecycle state machine, and CRUD.

Handlers stay thin; all rules live here. Tenant scoping is by ``workspace_id`` /
``org_id`` passed in by the API layer (resolved from the tenant context).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlmodel import Session, select

from app.core.errors import ConflictError, InvalidTransitionError, InvariantError, NotFoundError
from app.models.base import utcnow
from app.models.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentMetric, Metric, Variant
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentMetricAttach,
    ExperimentUpdate,
    VariantCreate,
)
from app.services.repository import add

ALLOCATION_TOLERANCE = 0.01

# Lifecycle: which target states are reachable from each status.
ALLOWED_TRANSITIONS: dict[ExperimentStatus, set[ExperimentStatus]] = {
    ExperimentStatus.draft: {ExperimentStatus.review, ExperimentStatus.archived},
    ExperimentStatus.review: {
        ExperimentStatus.draft,
        ExperimentStatus.running,
        ExperimentStatus.archived,
    },
    ExperimentStatus.running: {ExperimentStatus.paused, ExperimentStatus.concluded},
    ExperimentStatus.paused: {
        ExperimentStatus.running,
        ExperimentStatus.concluded,
        ExperimentStatus.archived,
    },
    ExperimentStatus.concluded: {ExperimentStatus.archived},
    ExperimentStatus.archived: set(),
}

# Config (variants, metrics, fields) may only change in these states.
EDITABLE_STATES = {ExperimentStatus.draft, ExperimentStatus.review}


class ExperimentInvariantError(InvariantError):
    """Variant/experiment invariant violation (maps to HTTP 422)."""


# --------------------------------------------------------------------------- invariants
def ensure_single_control(variants: Sequence[Variant]) -> None:
    controls = [v for v in variants if v.is_control]
    if len(controls) != 1:
        raise ExperimentInvariantError(
            f"exactly one control variant required, found {len(controls)}"
        )


def validate_variant_allocations(variants: Sequence[Variant]) -> None:
    if not variants:
        raise ExperimentInvariantError("at least one variant is required")
    total = sum(v.allocation_pct for v in variants)
    if abs(total - 100.0) > ALLOCATION_TOLERANCE:
        raise ExperimentInvariantError(f"variant allocations must sum to 100, got {total}")


def validate_variants(variants: Sequence[Variant]) -> None:
    validate_variant_allocations(variants)
    ensure_single_control(variants)


# --------------------------------------------------------------------------- reads
def get_experiment(session: Session, workspace_id: uuid.UUID, key: str) -> Experiment:
    exp = session.exec(
        select(Experiment).where(Experiment.workspace_id == workspace_id, Experiment.key == key)
    ).first()
    if exp is None:
        raise NotFoundError(f"experiment '{key}' not found")
    return exp


def list_experiments(
    session: Session, workspace_id: uuid.UUID, status: ExperimentStatus | None = None
) -> list[Experiment]:
    stmt = select(Experiment).where(Experiment.workspace_id == workspace_id)
    if status is not None:
        stmt = stmt.where(Experiment.status == status)
    return list(session.exec(stmt).all())


def get_variants(session: Session, experiment_id: uuid.UUID) -> list[Variant]:
    return list(session.exec(select(Variant).where(Variant.experiment_id == experiment_id)).all())


def get_experiment_metrics(session: Session, experiment_id: uuid.UUID) -> list[ExperimentMetric]:
    return list(
        session.exec(
            select(ExperimentMetric).where(ExperimentMetric.experiment_id == experiment_id)
        ).all()
    )


# --------------------------------------------------------------------------- writes
def create_experiment(
    session: Session,
    org_id: uuid.UUID,
    workspace_id: uuid.UUID,
    payload: ExperimentCreate,
) -> Experiment:
    existing = session.exec(
        select(Experiment).where(
            Experiment.workspace_id == workspace_id, Experiment.key == payload.key
        )
    ).first()
    if existing is not None:
        raise ConflictError(f"experiment key '{payload.key}' already exists in this workspace")

    experiment = Experiment(
        org_id=org_id,
        workspace_id=workspace_id,
        key=payload.key,
        name=payload.name,
        description=payload.description,
        hypothesis=payload.hypothesis,
        randomization_unit=payload.randomization_unit,
        layer_id=payload.layer_id,
        allocation=payload.allocation,
        targeting=payload.targeting,
        salt=payload.salt or payload.key,
    )
    variants = [
        Variant(
            org_id=org_id,
            key=v.key,
            name=v.name,
            is_control=v.is_control,
            allocation_pct=v.allocation_pct,
            payload=v.payload,
        )
        for v in payload.variants
    ]
    if variants:
        validate_variants(variants)

    add(session, experiment)
    for variant in variants:
        variant.experiment_id = experiment.id
        session.add(variant)
    session.commit()
    session.refresh(experiment)
    return experiment


def update_experiment(
    session: Session, workspace_id: uuid.UUID, key: str, payload: ExperimentUpdate
) -> Experiment:
    exp = get_experiment(session, workspace_id, key)
    if exp.status not in EDITABLE_STATES:
        raise ConflictError(f"cannot edit experiment in status '{exp.status}'")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exp, field, value)
    return add(session, exp)


def transition_experiment(
    session: Session, workspace_id: uuid.UUID, key: str, new_status: ExperimentStatus
) -> Experiment:
    exp = get_experiment(session, workspace_id, key)
    if new_status not in ALLOWED_TRANSITIONS[exp.status]:
        raise InvalidTransitionError(
            f"cannot transition experiment from '{exp.status}' to '{new_status}'"
        )
    if new_status == ExperimentStatus.running:
        validate_variants(get_variants(session, exp.id))
        if exp.start_at is None:
            exp.start_at = utcnow()
    if new_status == ExperimentStatus.concluded:
        exp.end_at = utcnow()
    exp.status = new_status
    return add(session, exp)


def add_variant(
    session: Session,
    org_id: uuid.UUID,
    workspace_id: uuid.UUID,
    key: str,
    payload: VariantCreate,
) -> Variant:
    exp = get_experiment(session, workspace_id, key)
    if exp.status not in EDITABLE_STATES:
        raise ConflictError(f"cannot add variants to experiment in status '{exp.status}'")
    duplicate = session.exec(
        select(Variant).where(Variant.experiment_id == exp.id, Variant.key == payload.key)
    ).first()
    if duplicate is not None:
        raise ConflictError(f"variant key '{payload.key}' already exists in this experiment")
    variant = Variant(
        org_id=org_id,
        experiment_id=exp.id,
        key=payload.key,
        name=payload.name,
        is_control=payload.is_control,
        allocation_pct=payload.allocation_pct,
        payload=payload.payload,
    )
    return add(session, variant)


def attach_metric(
    session: Session,
    org_id: uuid.UUID,
    workspace_id: uuid.UUID,
    key: str,
    payload: ExperimentMetricAttach,
) -> ExperimentMetric:
    exp = get_experiment(session, workspace_id, key)
    if exp.status not in EDITABLE_STATES:
        raise ConflictError(f"cannot change metrics on experiment in status '{exp.status}'")
    metric = session.exec(
        select(Metric).where(Metric.id == payload.metric_id, Metric.workspace_id == workspace_id)
    ).first()
    if metric is None:
        raise NotFoundError(f"metric {payload.metric_id} not found in this workspace")
    duplicate = session.exec(
        select(ExperimentMetric).where(
            ExperimentMetric.experiment_id == exp.id,
            ExperimentMetric.metric_id == payload.metric_id,
        )
    ).first()
    if duplicate is not None:
        raise ConflictError("metric already attached to this experiment")
    link = ExperimentMetric(
        org_id=org_id,
        experiment_id=exp.id,
        metric_id=payload.metric_id,
        role=payload.role,
        min_detectable_effect=payload.min_detectable_effect,
        is_oec=payload.is_oec,
    )
    return add(session, link)


# --------------------------------------------------------------------------- P02 helper
def create_experiment_with_variants(
    session: Session, experiment: Experiment, variants: list[Variant]
) -> Experiment:
    """Persist an experiment and its variants after checking invariants (used by tests)."""
    validate_variants(variants)
    if not experiment.salt:
        experiment.salt = experiment.key
    add(session, experiment)
    for variant in variants:
        variant.experiment_id = experiment.id
        variant.org_id = experiment.org_id
        session.add(variant)
    session.commit()
    session.refresh(experiment)
    return experiment
