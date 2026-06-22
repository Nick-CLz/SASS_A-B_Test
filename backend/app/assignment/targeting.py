"""Targeting / eligibility evaluation.

Targeting is a dict::

    {"match": "all" | "any", "rules": [{"attribute", "operator", "value"}]}

Empty / absent rules => eligible. Operators: eq, ne, in, not_in, exists, gt, gte, lt, lte.
Unknown attributes are treated as missing (every operator except ``exists`` fails).
"""

from __future__ import annotations

from typing import Any

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
    """Return True if ``attributes`` satisfy the targeting rules."""
    rules = targeting.get("rules") or []
    if not rules:
        return True
    results = [
        _compare(attributes.get(rule["attribute"], _MISSING), rule["operator"], rule.get("value"))
        for rule in rules
    ]
    return all(results) if targeting.get("match", "all") == "all" else any(results)
