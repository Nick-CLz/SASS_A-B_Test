"""Advanced stats: CUPED variance reduction + Bayesian conversion comparison."""

from __future__ import annotations

import numpy as np
import pytest
from app.stats.bayesian import beta_binomial_compare
from app.stats.frequentist import welch_t_test
from app.stats.results import MeanArm
from app.stats.variance_reduction import cuped


def _mean_arm(values: np.ndarray) -> MeanArm:
    return MeanArm(int(values.size), float(values.sum()), float((values * values).sum()))


def test_cuped_reduces_variance_and_is_unbiased() -> None:
    rng = np.random.default_rng(0)
    n, beta, noise = 4000, 2.0, 2.0  # corr(y, x)^2 ~ 0.5
    cx = rng.normal(0, 1, n)
    cy = 10.0 + beta * cx + rng.normal(0, noise, n)
    tx = rng.normal(0, 1, n)
    ty = 10.5 + beta * tx + rng.normal(0, noise, n)  # true effect +0.5

    plain = welch_t_test(_mean_arm(cy), _mean_arm(ty))
    adjusted = cuped(cy, cx, ty, tx)

    assert (adjusted.ci_upper - adjusted.ci_lower) < (plain.ci_upper - plain.ci_lower)
    assert adjusted.abs_effect == pytest.approx(0.5, abs=0.15)  # unbiased
    assert adjusted.method_detail["variance_reduction"] > 0.3


def test_cuped_uncorrelated_covariate_does_no_harm() -> None:
    rng = np.random.default_rng(1)
    n = 3000
    cx, cy = rng.normal(0, 1, n), rng.normal(10.0, 3, n)
    tx, ty = rng.normal(0, 1, n), rng.normal(10.5, 3, n)
    adjusted = cuped(cy, cx, ty, tx)
    assert adjusted.abs_effect == pytest.approx(0.5, abs=0.3)
    assert adjusted.method_detail["variance_reduction"] < 0.05  # rho ~ 0


def test_bayesian_clear_winner() -> None:
    res = beta_binomial_compare(2000, 200, 2000, 300)  # 10% vs 15%
    assert res.prob_treatment_better > 0.99
    assert res.expected_loss_ship_treatment < 1e-3
    assert res.ci_lower > 0  # credible interval for the difference excludes 0


def test_bayesian_no_difference_is_uncertain() -> None:
    res = beta_binomial_compare(2000, 200, 2000, 205)  # ~equal
    assert 0.3 < res.prob_treatment_better < 0.7
    assert res.ci_lower < 0 < res.ci_upper
