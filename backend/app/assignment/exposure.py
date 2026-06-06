"""Exposure logging hook.

The assignment endpoint records an *exposure* when a unit is assigned, so analysis can
count only exposed units (see docs/04-statistics-engine.md). Real persistence arrives with
ingestion in P06; until then a no-op sink is the default and an in-memory sink is used in
tests. The interface is what keeps P06 a drop-in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExposureEvent:
    workspace_id: str
    experiment_key: str
    variant_key: str
    unit_id: str


class ExposureSink(Protocol):
    def log(self, event: ExposureEvent) -> None: ...


class NullExposureSink:
    """Discards exposures (default until P06 wires real ingestion)."""

    def log(self, event: ExposureEvent) -> None:  # noqa: D102
        return None


class InMemoryExposureSink:
    """Collects exposures in a list (used in tests)."""

    def __init__(self) -> None:
        self.events: list[ExposureEvent] = []

    def log(self, event: ExposureEvent) -> None:
        self.events.append(event)
