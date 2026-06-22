"""Sequential (always-valid, peek-safe) + segment (HTE / Simpson's) tests."""

from __future__ import annotations

import numpy as np
from app.stats.results import ProportionArm
from app.stats.segments import segment_breakdown_proportions
from app.stats.sequential import msprt_pvalue


def test_msprt_aa_peeking_controls_fpr() -> None:
    """Peek constantly on A/A data: the ever-reject rate stays <= alpha (Ville)."""
    rng = np.random.default_rng(0)
    sims, length, alpha = 1000, 1500, 0.05
    grid = list(range(20, length + 1, 20))
    false_positives = 0
    for _ in range(sims):
        csum = np.cumsum(rng.normal(0, 1, length))
        if any(msprt_pvalue(n, float(csum[n - 1]), 1.0) < alpha for n in grid):
            false_positives += 1
    assert false_positives / sims <= 0.06  # <= alpha plus Monte-Carlo noise


def test_msprt_detects_real_effect() -> None:
    rng = np.random.default_rng(1)
    sims, length = 300, 4000
    grid = list(range(50, length + 1, 50))
    detections = 0
    for _ in range(sims):
        csum = np.cumsum(rng.normal(0.08, 1, length))
        if any(msprt_pvalue(n, float(csum[n - 1]), 1.0) < 0.05 for n in grid):
            detections += 1
    assert detections / sims > 0.8


def test_segment_simpsons_paradox_warning() -> None:
    # Treatment beats control in every segment, but loses pooled (Simpson's paradox).
    segments = {
        "A": (ProportionArm(100, 60), ProportionArm(6, 4)),
        "B": (ProportionArm(10, 3), ProportionArm(100, 36)),
    }
    breakdown = segment_breakdown_proportions(segments)
    assert breakdown.simpsons_warning
    assert breakdown.pooled.abs_effect < 0
    assert all(s.effect.abs_effect > 0 for s in breakdown.segments)


def test_segment_no_warning_when_consistent() -> None:
    segments = {
        "A": (ProportionArm(1000, 100), ProportionArm(1000, 150)),
        "B": (ProportionArm(1000, 120), ProportionArm(1000, 170)),
    }
    breakdown = segment_breakdown_proportions(segments)
    assert not breakdown.simpsons_warning
    assert len(breakdown.segments) == 2
