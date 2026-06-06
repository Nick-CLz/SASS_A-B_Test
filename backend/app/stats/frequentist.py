"""Frequentist tests: two-proportion z-test, Welch's t-test, Wilson interval, and the
delta-method relative-lift CI. Pure functions over sufficient statistics.

See docs/04-statistics-engine.md. Significance is "CI excludes 0" (and p < alpha).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import stats

from app.stats.results import EffectResult, MeanArm, ProportionArm


def z_critical(alpha: float) -> float:
    return float(stats.norm.ppf(1 - alpha / 2))


def wilson_interval(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a single proportion (better than Wald near 0/1)."""
    if n == 0:
        return (0.0, 0.0)
    z = z_critical(alpha)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (float(center - half), float(center + half))


def _relative_lift_ci(
    mean_c: float, mean_t: float, var_c_of_mean: float, var_t_of_mean: float, z: float
) -> tuple[float, float, float]:
    """Delta-method CI for relative lift = mean_t/mean_c - 1 (arms independent)."""
    if mean_c == 0:
        return (float("nan"), float("nan"), float("nan"))
    rel = mean_t / mean_c - 1.0
    var_rel = var_t_of_mean / mean_c**2 + (mean_t**2) * var_c_of_mean / mean_c**4
    se_rel = float(np.sqrt(var_rel))
    return (rel, rel - z * se_rel, rel + z * se_rel)


def two_proportion_z_test(
    control: ProportionArm, treatment: ProportionArm, alpha: float = 0.05
) -> EffectResult:
    """Two-proportion z-test (pooled) + Wald CI for the difference + delta-method lift."""
    n_c, n_t = control.n, treatment.n
    p_c, p_t = control.rate, treatment.rate
    diff = p_t - p_c

    p_pool = (control.successes + treatment.successes) / (n_c + n_t)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z_stat = diff / se_pool if se_pool > 0 else 0.0
    p_value = float(2 * stats.norm.sf(abs(z_stat)))

    se_diff = float(np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t))
    zc = z_critical(alpha)
    ci_lower, ci_upper = diff - zc * se_diff, diff + zc * se_diff

    rel, rel_lo, rel_hi = _relative_lift_ci(
        p_c, p_t, p_c * (1 - p_c) / n_c, p_t * (1 - p_t) / n_t, zc
    )
    is_sig = not (ci_lower <= 0 <= ci_upper)
    return EffectResult(
        estimate=p_t,
        control_estimate=p_c,
        abs_effect=diff,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        rel_effect=rel,
        rel_ci_lower=rel_lo,
        rel_ci_upper=rel_hi,
        p_value=p_value,
        std_error=se_diff,
        is_significant=is_sig,
        method="two_proportion_z",
        method_detail={"z": float(z_stat), "p_pool": float(p_pool), "alpha": alpha},
    )


def welch_t_test(control: MeanArm, treatment: MeanArm, alpha: float = 0.05) -> EffectResult:
    """Welch's t-test (unequal variances) + t CI for the difference + delta-method lift."""
    n_c, n_t = control.n, treatment.n
    m_c, m_t = control.mean, treatment.mean
    v_c, v_t = control.variance, treatment.variance
    diff = m_t - m_c

    se = float(np.sqrt(v_c / n_c + v_t / n_t))
    if v_c == 0 and v_t == 0:
        df = float(n_c + n_t - 2)
    else:
        df = (v_c / n_c + v_t / n_t) ** 2 / (
            (v_c / n_c) ** 2 / (n_c - 1) + (v_t / n_t) ** 2 / (n_t - 1)
        )
    t_stat = diff / se if se > 0 else 0.0
    p_value = float(2 * stats.t.sf(abs(t_stat), df))
    tc = float(stats.t.ppf(1 - alpha / 2, df))
    ci_lower, ci_upper = diff - tc * se, diff + tc * se

    rel, rel_lo, rel_hi = _relative_lift_ci(m_c, m_t, v_c / n_c, v_t / n_t, z_critical(alpha))
    is_sig = not (ci_lower <= 0 <= ci_upper)
    return EffectResult(
        estimate=m_t,
        control_estimate=m_c,
        abs_effect=diff,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        rel_effect=rel,
        rel_ci_lower=rel_lo,
        rel_ci_upper=rel_hi,
        p_value=p_value,
        std_error=se,
        is_significant=is_sig,
        method="welch_t",
        method_detail={"t": float(t_stat), "df": float(df), "alpha": alpha},
    )


def winsorize(
    values: Sequence[float], upper_pct: float = 0.01, lower_pct: float = 0.0
) -> np.ndarray:
    """Cap a heavy-tailed value array at the given quantiles (recorded as method detail)."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr
    lo = float(np.quantile(arr, lower_pct))
    hi = float(np.quantile(arr, 1 - upper_pct))
    clipped: np.ndarray = np.clip(arr, lo, hi)
    return clipped
