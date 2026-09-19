"""Frequentist engine: cross-checks vs scipy/statsmodels, A/A calibration, properties."""

from __future__ import annotations

import numpy as np
import pytest
from app.stats.frequentist import two_proportion_z_test, welch_t_test, wilson_interval
from app.stats.results import MeanArm, ProportionArm
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest


def _mean_arm(values: np.ndarray) -> MeanArm:
    return MeanArm(
        n=values.size, total=float(values.sum()), total_sq=float((values * values).sum())
    )


def test_welch_matches_scipy() -> None:
    rng = np.random.default_rng(0)
    control = rng.normal(10, 5, 500)
    treatment = rng.normal(11, 6, 480)
    res = welch_t_test(_mean_arm(control), _mean_arm(treatment))
    t, p = stats.ttest_ind(treatment, control, equal_var=False)
    assert res.method_detail["t"] == pytest.approx(float(t), rel=1e-6)
    assert res.p_value == pytest.approx(float(p), rel=1e-6)


def test_two_proportion_matches_statsmodels() -> None:
    res = two_proportion_z_test(ProportionArm(1000, 100), ProportionArm(1000, 130))
    z, p = proportions_ztest([130, 100], [1000, 1000])
    assert res.method_detail["z"] == pytest.approx(float(z), rel=1e-6)
    assert res.p_value == pytest.approx(float(p), rel=1e-6)


def test_wilson_interval_known_value() -> None:
    lo, hi = wilson_interval(50, 100, 0.05)
    assert lo == pytest.approx(0.4038, abs=1e-3)
    assert hi == pytest.approx(0.5962, abs=1e-3)


def test_more_data_tightens_ci() -> None:
    small = two_proportion_z_test(ProportionArm(100, 10), ProportionArm(100, 13))
    large = two_proportion_z_test(ProportionArm(10000, 1000), ProportionArm(10000, 1300))
    assert (large.ci_upper - large.ci_lower) < (small.ci_upper - small.ci_lower)


def test_aa_calibration_uniform_pvalues_and_fpr() -> None:
    """A/A: over many null experiments p-values are ~uniform and the FPR ~= alpha."""
    rng = np.random.default_rng(42)
    n_experiments, n, rate, alpha = 800, 1000, 0.1, 0.05
    pvalues = []
    false_positives = 0
    for _ in range(n_experiments):
        control = int(rng.binomial(n, rate))
        treatment = int(rng.binomial(n, rate))
        res = two_proportion_z_test(ProportionArm(n, control), ProportionArm(n, treatment), alpha)
        pvalues.append(res.p_value)
        false_positives += res.p_value < alpha
    fpr = false_positives / n_experiments
    assert 0.03 <= fpr <= 0.075  # close to alpha=0.05
    assert stats.kstest(pvalues, "uniform").pvalue > 0.01  # ~uniform


def test_significant_when_effect_is_large() -> None:
    res = two_proportion_z_test(ProportionArm(5000, 500), ProportionArm(5000, 750))
    assert res.is_significant
    assert res.p_value < 0.001
    assert res.rel_effect == pytest.approx(0.5, abs=0.02)  # 15% vs 10% -> +50% lift
