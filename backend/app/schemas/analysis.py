"""Analysis / results request & response schemas (see docs/06-api-and-sdk.md §Results)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    alpha: float = 0.05
    correction: str = "benjamini_hochberg"  # bonferroni | holm | benjamini_hochberg | none


class SrmRead(BaseModel):
    chi_square: float
    p_value: float
    is_mismatch: bool
    observed: dict[str, int]
    expected: dict[str, float]


class MetricResultRead(BaseModel):
    metric_key: str
    variant_key: str
    is_control: bool
    n: int
    estimate: float | None
    abs_effect: float | None
    rel_effect: float | None
    ci_lower: float | None
    ci_upper: float | None
    p_value: float | None
    is_significant: bool
    method_detail: dict[str, Any] = Field(default_factory=dict)


class AnalysisRunRead(BaseModel):
    id: uuid.UUID
    computed_at: datetime
    status: str
    method: dict[str, Any]
    srm: SrmRead | None
    results: list[MetricResultRead]


class PowerResponse(BaseModel):
    baseline: float
    mde: float
    alpha: float
    power: float
    sample_size_per_arm: int
    total_sample_size: int
    runtime_days: int | None
