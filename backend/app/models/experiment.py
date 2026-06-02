"""Experiment configuration: layer, metric, experiment, variant, experiment-metric link."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import Base, enum_type, json_type
from app.models.enums import (
    ExperimentDecision,
    ExperimentMetricRole,
    ExperimentStatus,
    MetricDirection,
    MetricType,
    RandomizationUnit,
)


class Layer(Base, table=True):
    __tablename__ = "layer"

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    name: str
    # Mutual-exclusion + holdout partitions (see docs/04-statistics-engine.md#assignment).
    traffic_partitions: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())


class Metric(Base, table=True):
    __tablename__ = "metric"
    __table_args__ = (UniqueConstraint("workspace_id", "key", name="uq_metric_workspace_key"),)

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    key: str
    name: str
    type: MetricType = Field(sa_type=enum_type(MetricType))
    numerator: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    denominator: dict[str, Any] | None = Field(default=None, sa_type=json_type())
    direction: MetricDirection = Field(
        default=MetricDirection.increase_good, sa_type=enum_type(MetricDirection)
    )
    unit: str | None = None
    winsorize_pct: float | None = None


class Experiment(Base, table=True):
    __tablename__ = "experiment"
    __table_args__ = (UniqueConstraint("workspace_id", "key", name="uq_experiment_workspace_key"),)

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    key: str = Field(index=True)
    name: str
    description: str = ""
    hypothesis: str = ""
    status: ExperimentStatus = Field(
        default=ExperimentStatus.draft, sa_type=enum_type(ExperimentStatus)
    )
    layer_id: uuid.UUID | None = Field(default=None, foreign_key="layer.id")
    randomization_unit: RandomizationUnit = Field(
        default=RandomizationUnit.user_id, sa_type=enum_type(RandomizationUnit)
    )
    allocation: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    targeting: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    salt: str = ""
    seed: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    decision: ExperimentDecision | None = Field(default=None, sa_type=enum_type(ExperimentDecision))


class Variant(Base, table=True):
    __tablename__ = "variant"
    __table_args__ = (UniqueConstraint("experiment_id", "key", name="uq_variant_experiment_key"),)

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    experiment_id: uuid.UUID = Field(foreign_key="experiment.id", index=True)
    key: str
    name: str = ""
    is_control: bool = False
    allocation_pct: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())


class ExperimentMetric(Base, table=True):
    __tablename__ = "experiment_metric"
    __table_args__ = (
        UniqueConstraint("experiment_id", "metric_id", name="uq_expmetric_exp_metric"),
    )

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    experiment_id: uuid.UUID = Field(foreign_key="experiment.id", index=True)
    metric_id: uuid.UUID = Field(foreign_key="metric.id", index=True)
    role: ExperimentMetricRole = Field(
        default=ExperimentMetricRole.secondary, sa_type=enum_type(ExperimentMetricRole)
    )
    min_detectable_effect: float | None = None
    is_oec: bool = False
