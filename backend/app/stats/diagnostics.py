"""Data-quality + multiplicity diagnostics: SRM and multiple-comparison correction.

SRM is the most important guardrail — a mismatch means the experiment is broken and results
must not be trusted (docs/04-statistics-engine.md §Diagnostics). Pure functions.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import stats

from app.stats.results import SrmResult

# A deliberately strict default so noise doesn't flag healthy experiments.
SRM_ALPHA = 0.001


def srm_check(
    observed: dict[str, int], allocation: dict[str, float], alpha: float = SRM_ALPHA
) -> SrmResult:
    """Chi-square goodness-of-fit of observed arm counts vs. the intended allocation."""
    keys = list(observed)
    obs = np.array([observed[k] for k in keys], dtype=float)
    ratio = np.array([allocation[k] for k in keys], dtype=float)
    ratio = ratio / ratio.sum()
    expected = obs.sum() * ratio
    chi_square = float(((obs - expected) ** 2 / expected).sum())
    df = len(keys) - 1
    p_value = float(stats.chi2.sf(chi_square, df)) if df > 0 else 1.0
    return SrmResult(
        chi_square=chi_square,
        p_value=p_value,
        df=df,
        observed=observed,
        expected={k: float(e) for k, e in zip(keys, expected, strict=True)},
        is_mismatch=p_value < alpha,
    )


def bonferroni(pvalues: Sequence[float], alpha: float = 0.05) -> list[tuple[bool, float]]:
    """Family-wise (Bonferroni): adjusted p = min(p*m, 1)."""
    m = len(pvalues)
    return [(min(p * m, 1.0) <= alpha, min(p * m, 1.0)) for p in pvalues]


def holm(pvalues: Sequence[float], alpha: float = 0.05) -> list[tuple[bool, float]]:
    """Holm step-down (family-wise), returning (reject, adjusted_p) in input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, pvalues[i] * (m - rank))
        adjusted[i] = min(running, 1.0)
    return [(adjusted[i] <= alpha, adjusted[i]) for i in range(m)]


def benjamini_hochberg(pvalues: Sequence[float], alpha: float = 0.05) -> list[tuple[bool, float]]:
    """Benjamini-Hochberg FDR control, returning (reject, adjusted_p) in input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    prev = 1.0
    for rank in reversed(range(m)):
        i = order[rank]
        prev = min(prev, pvalues[i] * m / (rank + 1))
        adjusted[i] = min(prev, 1.0)
    return [(adjusted[i] <= alpha, adjusted[i]) for i in range(m)]
