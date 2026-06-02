"""SQLModel metadata tables (see docs/03-data-model.md). Implemented in P02.

Importing this package registers every table on ``SQLModel.metadata`` (used by Alembic
autogenerate and by ``create_all`` in tests).
"""

from app.models.agent import AgentRun, AgentStep
from app.models.analysis import AnalysisRun, MetricResult, Readout, SrmCheck
from app.models.base import Base, enum_type, json_type, utcnow, uuid7
from app.models.experiment import (
    Experiment,
    ExperimentMetric,
    Layer,
    Metric,
    Variant,
)
from app.models.org import (
    ApiKey,
    AuditLog,
    Membership,
    Organization,
    User,
    Workspace,
)

__all__ = [
    # base helpers
    "Base",
    "enum_type",
    "json_type",
    "utcnow",
    "uuid7",
    # org / identity
    "Organization",
    "User",
    "Workspace",
    "Membership",
    "ApiKey",
    "AuditLog",
    # experiment config
    "Layer",
    "Metric",
    "Experiment",
    "Variant",
    "ExperimentMetric",
    # analysis / results
    "AnalysisRun",
    "MetricResult",
    "SrmCheck",
    "Readout",
    # agents
    "AgentRun",
    "AgentStep",
]
