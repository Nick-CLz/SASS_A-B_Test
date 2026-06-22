"""Layer service (mutual-exclusion groups / holdouts, workspace-scoped)."""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.models.experiment import Layer
from app.schemas.layer import LayerCreate
from app.services.repository import add


def create_layer(
    session: Session, org_id: uuid.UUID, workspace_id: uuid.UUID, payload: LayerCreate
) -> Layer:
    layer = Layer(
        org_id=org_id,
        workspace_id=workspace_id,
        name=payload.name,
        traffic_partitions=payload.traffic_partitions,
    )
    return add(session, layer)


def list_layers(session: Session, workspace_id: uuid.UUID) -> list[Layer]:
    return list(session.exec(select(Layer).where(Layer.workspace_id == workspace_id)).all())
