"""Pure specifications consumed by the assignment engine.

These are deliberately decoupled from the DB models so the engine stays pure and
cacheable. The API layer builds them from ``Experiment`` / ``Variant`` / ``Layer`` rows.
See docs/04-statistics-engine.md#assignment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VariantSpec:
    key: str
    allocation_pct: float


@dataclass(frozen=True)
class LayerSlot:
    """An experiment's reserved sub-range ``[start, end)`` within its layer's hash space."""

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
    """Result of evaluating one experiment for one unit."""

    experiment_key: str
    eligible: bool
    in_experiment: bool
    variant_key: str | None
    reason: str

    @property
    def payload_key(self) -> str | None:
        return self.variant_key
