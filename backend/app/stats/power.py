"""Power & sample size (proportions and means) + runtime from traffic. Pure functions.

See docs/04-statistics-engine.md §Power. The Designer agent (P12) calls these so a defensible
duration is computed, never guessed.
"""

from __future__ import annotations

import math

from scipy import stats


def _z_alpha(alpha: float) -> float:
    return float(stats.norm.ppf(1 - alpha / 2))


def _z_power(power: float) -> float:
    return float(stats.norm.ppf(power))


def sample_size_proportion(
    baseline: float, mde_abs: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Per-arm sample size to detect an absolute lift ``mde_abs`` over ``baseline``."""
    if mde_abs <= 0:
        raise ValueError("mde_abs must be > 0")
    p1, p2 = baseline, baseline + mde_abs
    p_bar = (p1 + p2) / 2
    za, zb = _z_alpha(alpha), _z_power(power)
    numerator = (
        za * math.sqrt(2 * p_bar * (1 - p_bar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    return math.ceil(numerator / mde_abs**2)


def sample_size_mean(sigma: float, mde_abs: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Per-arm sample size to detect a mean difference ``mde_abs`` given std ``sigma``."""
    if mde_abs <= 0:
        raise ValueError("mde_abs must be > 0")
    za, zb = _z_alpha(alpha), _z_power(power)
    return math.ceil(2 * sigma**2 * (za + zb) ** 2 / mde_abs**2)


def mde_proportion(
    baseline: float, n_per_arm: int, alpha: float = 0.05, power: float = 0.8
) -> float:
    """Smallest absolute lift detectable at a given per-arm sample size (approximate)."""
    za, zb = _z_alpha(alpha), _z_power(power)
    return (za + zb) * math.sqrt(2 * baseline * (1 - baseline) / n_per_arm)


def runtime_days(total_units_required: int, daily_units: float) -> int:
    """Days to accrue the required total units at an observed daily rate."""
    if daily_units <= 0:
        return 0
    return math.ceil(total_units_required / daily_units)
