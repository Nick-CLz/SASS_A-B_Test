"""Power: simulation confirms the sample-size formula achieves the target power."""

from __future__ import annotations

import numpy as np
from app.stats.frequentist import two_proportion_z_test
from app.stats.power import mde_proportion, sample_size_mean, sample_size_proportion
from app.stats.results import ProportionArm


def test_power_simulation_proportion() -> None:
    baseline, mde, alpha, power = 0.10, 0.03, 0.05, 0.80
    n = sample_size_proportion(baseline, mde, alpha, power)
    rng = np.random.default_rng(1)
    trials, rejects = 600, 0
    for _ in range(trials):
        control = int(rng.binomial(n, baseline))
        treatment = int(rng.binomial(n, baseline + mde))
        res = two_proportion_z_test(ProportionArm(n, control), ProportionArm(n, treatment), alpha)
        rejects += res.p_value < alpha
    achieved = rejects / trials
    assert abs(achieved - power) < 0.06  # within ~6pp of the target power


def test_sample_size_monotonic_in_mde() -> None:
    assert sample_size_proportion(0.1, 0.01) > sample_size_proportion(0.1, 0.05)
    assert sample_size_mean(5.0, 0.5) > sample_size_mean(5.0, 1.0)


def test_mde_and_sample_size_are_consistent() -> None:
    baseline, n = 0.10, sample_size_proportion(0.10, 0.03)
    recovered = mde_proportion(baseline, n)
    assert recovered < 0.03 + 0.005  # the MDE at that n is about the design MDE
