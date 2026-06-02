"""Results tables: analysis runs, metric results, SRM checks, readouts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import Base, enum_type, json_type, utcnow
from app.models.enums import (
    AnalysisStatus,
    AnalysisTrigger,
    ExperimentDecision,
    ReadoutAuthor,
)


class AnalysisRun(Base, table=True):
    __tablename__ = "analysis_run"

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    experiment_id: uuid.UUID = Field(foreign_key="experiment.id", index=True)
    computed_at: datetime = Field(default_factory=utcnow)
    method: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    window_start: datetime | None = None
    window_end: datetime | None = None
    trigger: AnalysisTrigger = Field(
        default=AnalysisTrigger.manual, sa_type=enum_type(AnalysisTrigger)
    )
    status: AnalysisStatus = Field(
        default=AnalysisStatus.pending, sa_type=enum_type(AnalysisStatus)
    )


class MetricResult(Base, table=True):
    __tablename__ = "metric_result"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id",
            "metric_id",
            "variant_id",
            name="uq_metricresult_run_metric_variant",
        ),
    )

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    analysis_run_id: uuid.UUID = Field(foreign_key="analysis_run.id", index=True)
    metric_id: uuid.UUID = Field(foreign_key="metric.id", index=True)
    variant_id: uuid.UUID = Field(foreign_key="variant.id", index=True)
    n: int = 0
    estimate: float | None = None
    abs_effect: float | None = None
    rel_effect: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    p_value: float | None = None
    prob_to_beat_control: float | None = None
    expected_loss: float | None = None
    variance: float | None = None
    std_error: float | None = None
    is_significant: bool = False
    method_detail: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())


class SrmCheck(Base, table=True):
    __tablename__ = "srm_check"

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    analysis_run_id: uuid.UUID = Field(foreign_key="analysis_run.id", unique=True, index=True)
    chi_square: float
    p_value: float
    observed: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    expected: dict[str, Any] = Field(default_factory=dict, sa_type=json_type())
    is_mismatch: bool = False


class Readout(Base, table=True):
    __tablename__ = "readout"

    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    experiment_id: uuid.UUID = Field(foreign_key="experiment.id", index=True)
    analysis_run_id: uuid.UUID | None = Field(default=None, foreign_key="analysis_run.id")
    author_kind: ReadoutAuthor = Field(
        default=ReadoutAuthor.agent, sa_type=enum_type(ReadoutAuthor)
    )
    author_user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    decision_recommendation: ExperimentDecision | None = Field(
        default=None, sa_type=enum_type(ExperimentDecision)
    )
    confidence: float | None = None
    body_markdown: str = ""
    # Each source ties a claim back to a tool call / result row (grounding).
    sources: list[dict[str, Any]] = Field(default_factory=list, sa_type=json_type())
