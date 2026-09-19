"""Sequential / always-valid inference — peek any time without inflating Type I error.

Implements the mSPRT (mixture Sequential Probability Ratio Test) always-valid p-value for a
one-sample mean (H0: mean = 0) with a N(0, tau^2) mixing prior. By Ville's inequality,
P(inf_n p_n < alpha | H0) <= alpha, so stopping the first time ``p_n < alpha`` controls the
false-positive rate at *every* stopping time — the basis of "peek-safe" monitoring (a
two-sample difference is fed in as a centered stream). See docs/04 §Sequential. Pure.
"""

from __future__ import annotations

import math


def msprt_pvalue(n: int, sum_x: float, variance: float, tau2: float | None = None) -> float:
    """Always-valid p-value for H0: mean = 0 from cumulative ``(n, sum_x)``.

    ``variance`` is the per-observation variance; ``tau2`` is the mixing scale (defaults to
    ``variance``). Returns a value in (0, 1] that is valid simultaneously over all ``n``.
    """
    if n <= 0 or variance <= 0:
        return 1.0
    sigma2 = variance
    if tau2 is None:
        tau2 = sigma2
    a = n / (2 * sigma2) + 1 / (2 * tau2)
    b = sum_x / sigma2
    log_lambda = -0.5 * math.log(2 * tau2 * a) + (b * b) / (4 * a)
    return min(1.0, math.exp(-log_lambda))
