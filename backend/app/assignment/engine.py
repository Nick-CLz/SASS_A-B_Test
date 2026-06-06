"""The deterministic assignment engine (pure, no I/O).

Order of evaluation: targeting -> layer/traffic gate -> variant split.
See docs/04-statistics-engine.md#assignment.
"""

from __future__ import annotations

from typing import Any

from app.assignment.bucketing import bucket
from app.assignment.spec import Assignment, ExperimentSpec, VariantSpec
from app.assignment.targeting import evaluate_targeting


def _pick_variant(variants: tuple[VariantSpec, ...], point_0_1: float) -> str | None:
    total = sum(v.allocation_pct for v in variants)
    if total <= 0:
        return None
    point = point_0_1 * total
    cumulative = 0.0
    for variant in variants:
        cumulative += variant.allocation_pct
        if point < cumulative:
            return variant.key
    return variants[-1].key  # floating-point guard


def assign(
    spec: ExperimentSpec, unit_id: str, attributes: dict[str, Any] | None = None
) -> Assignment:
    """Assign ``unit_id`` to a variant of ``spec`` (or report why not)."""
    attrs = attributes or {}

    if not evaluate_targeting(attrs, spec.targeting):
        return Assignment(spec.key, False, False, None, "not_eligible")

    if spec.layer is not None:
        slot = bucket(spec.layer.salt, unit_id)
        if not (spec.layer.start <= slot < spec.layer.end):
            return Assignment(spec.key, True, False, None, "not_in_layer")
    else:
        traffic = bucket(f"{spec.salt}:traffic", unit_id)
        if traffic >= spec.traffic_pct / 100.0:
            return Assignment(spec.key, True, False, None, "not_in_traffic")

    variant_key = _pick_variant(spec.variants, bucket(f"{spec.salt}:variant", unit_id))
    if variant_key is None:
        return Assignment(spec.key, True, False, None, "no_variants")
    return Assignment(spec.key, True, True, variant_key, "assigned")
