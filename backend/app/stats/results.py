"""Typed inputs and outputs for the statistics engine (pure data, no I/O).

Inputs are **sufficient statistics** (counts/sums/sums-of-squares) — the only thing that
crosses from the analytics layer — so the engine stays pure and testable. Outputs map onto
``metric_result`` / ``srm_check`` in docs/03-data-model.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProportionArm:
    """Sufficient statistics for a binary (conversion) metric in one arm."""

    n: int
    successes: int

    @property
    def rate(self) -> float:
        return self.successes / self.n if self.n else 0.0


@dataclass(frozen=True)
class MeanArm:
    """Sufficient statistics for a continuous metric in one arm."""

    n: int
    total: float
    total_sq: float

    @property
    def mean(self) -> float:
        return self.total / self.n if self.n else 0.0

    @property
    def variance(self) -> float:
        """Unbiased sample variance from sufficient statistics."""
        if self.n < 2:
            return 0.0
        var = (self.total_sq - self.total**2 / self.n) / (self.n - 1)
        return max(var, 0.0)


@dataclass(frozen=True)
class EffectResult:
    """A treatment-vs-control comparison for one metric (maps to ``metric_result``)."""

    estimate: float  # treatment point estimate
    control_estimate: float
    abs_effect: float
    ci_lower: float
    ci_upper: float
    rel_effect: float
    rel_ci_lower: float
    rel_ci_upper: float
    p_value: float
    std_error: float
    is_significant: bool
    method: str
    method_detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SrmResult:
    """Sample-ratio-mismatch chi-square result (maps to ``srm_check``)."""

    chi_square: float
    p_value: float
    df: int
    observed: dict[str, int]
    expected: dict[str, float]
    is_mismatch: bool
