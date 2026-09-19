"""Local assignment — mirrors ``backend/app/assignment/engine.py`` exactly."""

from __future__ import annotations

from typing import Any

from mallard_sdk.bucketing import bucket
from mallard_sdk.spec import Assignment, ExperimentSpec, VariantSpec

_MISSING = object()


def _compare(actual: Any, operator: str, value: Any) -> bool:
    if operator == "exists":
        return actual is not _MISSING
    if actual is _MISSING:
        return False
    try:
        if operator == "eq":
            return bool(actual == value)
        if operator == "ne":
            return bool(actual != value)
        if operator == "in":
            return actual in value
        if operator == "not_in":
            return actual not in value
        if operator == "gt":
            return bool(actual > value)
        if operator == "gte":
            return bool(actual >= value)
        if operator == "lt":
            return bool(actual < value)
        if operator == "lte":
            return bool(actual <= value)
    except TypeError:
        return False
    raise ValueError(f"unknown targeting operator: {operator!r}")


def evaluate_targeting(attributes: dict[str, Any], targeting: dict[str, Any]) -> bool:
    rules = targeting.get("rules") or []
    if not rules:
        return True
    results = [
        _compare(attributes.get(r["attribute"], _MISSING), r["operator"], r.get("value"))
        for r in rules
    ]
    return all(results) if targeting.get("match", "all") == "all" else any(results)


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
    return variants[-1].key


def assign(
    spec: ExperimentSpec, unit_id: str, attributes: dict[str, Any] | None = None
) -> Assignment:
    attrs = attributes or {}
    if not evaluate_targeting(attrs, spec.targeting):
        return Assignment(spec.key, False, False, None, "not_eligible")
    if spec.layer is not None:
        slot = bucket(spec.layer.salt, unit_id)
        if not (spec.layer.start <= slot < spec.layer.end):
            return Assignment(spec.key, True, False, None, "not_in_layer")
    else:
        if bucket(f"{spec.salt}:traffic", unit_id) >= spec.traffic_pct / 100.0:
            return Assignment(spec.key, True, False, None, "not_in_traffic")
    variant_key = _pick_variant(spec.variants, bucket(f"{spec.salt}:variant", unit_id))
    if variant_key is None:
        return Assignment(spec.key, True, False, None, "no_variants")
    return Assignment(spec.key, True, True, variant_key, "assigned")
