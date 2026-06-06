"""Variance reduction: CUPED (Controlled experiment Using Pre-Existing Data).

Uses a pre-period covariate ``x`` to remove explainable variance from the outcome ``y``:
``y_cuped = y - theta * (x - mean_x)`` with ``theta = Cov(y, x) / Var(x)``. Unbiased, and it
reduces variance by ~rho^2 (the squared y-x correlation) — tighter CIs with the same users.
See docs/04-statistics-engine.md §CUPED. Pure (operates on per-unit arrays).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

import numpy as np

from app.stats.frequentist import welch_t_test
from app.stats.results import EffectResult, MeanArm


def cuped_theta(y: np.ndarray, x: np.ndarray) -> float:
    """theta = Cov(y, x) / Var(x), estimated on pooled (both-arm) data."""
    var_x = float(np.var(x, ddof=1))
    if var_x == 0:
        return 0.0
    return float(np.cov(y, x, ddof=1)[0, 1] / var_x)


def _mean_arm(values: np.ndarray) -> MeanArm:
    return MeanArm(
        n=int(values.size), total=float(values.sum()), total_sq=float((values * values).sum())
    )


def cuped(
    control_y: Sequence[float],
    control_x: Sequence[float],
    treatment_y: Sequence[float],
    treatment_x: Sequence[float],
    alpha: float = 0.05,
) -> EffectResult:
    """CUPED-adjusted Welch test. ``x`` is a pre-experiment covariate (no treatment effect)."""
    cy, cx = np.asarray(control_y, float), np.asarray(control_x, float)
    ty, tx = np.asarray(treatment_y, float), np.asarray(treatment_x, float)
    y_all = np.concatenate([cy, ty])
    x_all = np.concatenate([cx, tx])

    theta = cuped_theta(y_all, x_all)
    x_mean = float(x_all.mean())
    control = _mean_arm(cy - theta * (cx - x_mean))
    treatment = _mean_arm(ty - theta * (tx - x_mean))

    result = welch_t_test(control, treatment, alpha)
    var_x = float(np.var(x_all, ddof=1))
    var_y = float(np.var(y_all, ddof=1))
    rho = (
        float(np.cov(y_all, x_all, ddof=1)[0, 1] / np.sqrt(var_x * var_y))
        if var_x * var_y > 0
        else 0.0
    )
    return replace(
        result,
        method="cuped",
        method_detail={
            **result.method_detail,
            "theta": theta,
            "rho": rho,
            "variance_reduction": rho**2,
        },
    )
