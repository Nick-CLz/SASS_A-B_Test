"""Metric definition service (reusable, workspace-scoped)."""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.core.errors import ConflictError, NotFoundError
from app.models.experiment import Metric
from app.schemas.metric import MetricCreate
from app.services.repository import add


def create_metric(
    session: Session, org_id: uuid.UUID, workspace_id: uuid.UUID, payload: MetricCreate
) -> Metric:
    existing = session.exec(
        select(Metric).where(Metric.workspace_id == workspace_id, Metric.key == payload.key)
    ).first()
    if existing is not None:
        raise ConflictError(f"metric key '{payload.key}' already exists in this workspace")
    metric = Metric(
        org_id=org_id,
        workspace_id=workspace_id,
        key=payload.key,
        name=payload.name,
        type=payload.type,
        numerator=payload.numerator,
        denominator=payload.denominator,
        direction=payload.direction,
        unit=payload.unit,
        winsorize_pct=payload.winsorize_pct,
    )
    return add(session, metric)


def list_metrics(session: Session, workspace_id: uuid.UUID) -> list[Metric]:
    return list(session.exec(select(Metric).where(Metric.workspace_id == workspace_id)).all())


def get_metric(session: Session, workspace_id: uuid.UUID, metric_id: uuid.UUID) -> Metric:
    metric = session.exec(
        select(Metric).where(Metric.id == metric_id, Metric.workspace_id == workspace_id)
    ).first()
    if metric is None:
        raise NotFoundError(f"metric {metric_id} not found")
    return metric
