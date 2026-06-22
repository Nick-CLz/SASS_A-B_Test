"""Local experiment specs + assignment result (mirrors the server's shapes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VariantSpec:
    key: str
    allocation_pct: float


@dataclass(frozen=True)
class LayerSlot:
    salt: str
    start: float
    end: float


@dataclass(frozen=True)
class ExperimentSpec:
    key: str
    salt: str
    variants: tuple[VariantSpec, ...]
    traffic_pct: float = 100.0
    targeting: dict[str, Any] = field(default_factory=dict)
    layer: LayerSlot | None = None


@dataclass(frozen=True)
class Assignment:
    experiment_key: str
    eligible: bool
    in_experiment: bool
    variant_key: str | None
    reason: str
