"""Assignment service: build cached experiment specs from the DB and assign units.

The pure engine (``app.assignment``) does the math; this layer maps DB rows to specs,
caches them per workspace, and records exposures.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session, select

from app.assignment import Assignment, ExperimentSpec, LayerSlot, VariantSpec, assign
from app.assignment.cache import get_cached, set_cached
from app.assignment.exposure import ExposureEvent, ExposureSink
from app.core.errors import NotFoundError
from app.models.enums import ExperimentStatus
from app.models.experiment import Experiment, Variant


def build_specs(session: Session, workspace_id: uuid.UUID) -> list[ExperimentSpec]:
    """Build specs for every *running* experiment in the workspace."""
    experiments = session.exec(
        select(Experiment).where(
            Experiment.workspace_id == workspace_id,
            Experiment.status == ExperimentStatus.running,
        )
    ).all()
    specs: list[ExperimentSpec] = []
    for exp in experiments:
        variants = session.exec(select(Variant).where(Variant.experiment_id == exp.id)).all()
        allocation: dict[str, Any] = exp.allocation or {}
        layer: LayerSlot | None = None
        if exp.layer_id is not None:
            start, end = allocation.get("layer_range", [0.0, 1.0])
            layer = LayerSlot(str(exp.layer_id), float(start), float(end))
        specs.append(
            ExperimentSpec(
                key=exp.key,
                salt=exp.salt or exp.key,
                variants=tuple(VariantSpec(v.key, v.allocation_pct) for v in variants),
                traffic_pct=float(allocation.get("traffic_pct", 100.0)),
                targeting=exp.targeting or {},
                layer=layer,
            )
        )
    return specs


def get_specs(session: Session, workspace_id: uuid.UUID) -> list[ExperimentSpec]:
    """Return cached specs for the workspace, building (and caching) on a miss."""
    cached = get_cached(workspace_id)
    if cached is not None:
        return cached
    specs = build_specs(session, workspace_id)
    set_cached(workspace_id, specs)
    return specs


def assign_unit(
    session: Session,
    workspace_id: uuid.UUID,
    unit_id: str,
    attributes: dict[str, Any] | None = None,
    experiment_key: str | None = None,
    sink: ExposureSink | None = None,
    log_exposure: bool = True,
) -> list[Assignment]:
    """Assign a unit across running experiments (or one named experiment)."""
    specs = get_specs(session, workspace_id)
    if experiment_key is not None:
        specs = [s for s in specs if s.key == experiment_key]
        if not specs:
            raise NotFoundError(f"running experiment '{experiment_key}' not found")

    results = [assign(spec, unit_id, attributes) for spec in specs]

    if log_exposure and sink is not None:
        for result in results:
            if result.in_experiment and result.variant_key is not None:
                sink.log(
                    ExposureEvent(
                        workspace_id=str(workspace_id),
                        experiment_key=result.experiment_key,
                        variant_key=result.variant_key,
                        unit_id=unit_id,
                    )
                )
    return results
