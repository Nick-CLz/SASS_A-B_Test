"""Heterogeneous treatment effects: per-segment breakdown with multiple-comparison control
and a Simpson's-paradox warning (pooled effect sign disagrees with every segment). Pure.

See docs/04 §Heterogeneous treatment effects.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.stats.diagnostics import benjamini_hochberg
from app.stats.frequentist import two_proportion_z_test
from app.stats.results import EffectResult, ProportionArm


@dataclass(frozen=True)
class SegmentEffect:
    segment: str
    effect: EffectResult
    is_significant: bool  # after FDR correction across segments


@dataclass(frozen=True)
class SegmentBreakdown:
    segments: list[SegmentEffect]
    pooled: EffectResult
    simpsons_warning: bool


def segment_breakdown_proportions(
    segments: dict[str, tuple[ProportionArm, ProportionArm]],
    alpha: float = 0.05,
) -> SegmentBreakdown:
    """Per-segment two-proportion tests with FDR correction + a Simpson's-paradox check.

    ``segments`` maps a segment name to ``(control_arm, treatment_arm)``.
    """
    names = list(segments)
    effects = [two_proportion_z_test(segments[name][0], segments[name][1], alpha) for name in names]
    corrected = benjamini_hochberg([e.p_value for e in effects], alpha)
    seg_effects = [
        SegmentEffect(name, effect, reject)
        for name, effect, (reject, _adj) in zip(names, effects, corrected, strict=True)
    ]

    pooled_control = ProportionArm(
        sum(segments[n][0].n for n in names), sum(segments[n][0].successes for n in names)
    )
    pooled_treatment = ProportionArm(
        sum(segments[n][1].n for n in names), sum(segments[n][1].successes for n in names)
    )
    pooled = two_proportion_z_test(pooled_control, pooled_treatment, alpha)

    pooled_positive = pooled.abs_effect > 0
    simpsons = (
        len(effects) > 1
        and abs(pooled.abs_effect) > 1e-9
        and all((e.abs_effect > 0) != pooled_positive for e in effects)
    )
    return SegmentBreakdown(seg_effects, pooled, simpsons)
