"""The ``AnalyticsBackend`` interface: the contract every analytics store implements.

A backend returns **only sufficient statistics** (counts, sums, sums-of-squares) — never raw
rows — so the stats engine stays pure and the *same* analysis runs on any backend: DuckDB
embedded (``DuckStore``) or a SQL warehouse (``SqlStore``). See docs/02-architecture.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

# (exposure_id, workspace_id, experiment_key, variant_key, unit_id, ts, attrs_json)
ExposureRow = tuple[str, str, str, str, str, datetime, str]
# (event_id, workspace_id, unit_id, name, ts, value, props_json)
EventRow = tuple[str, str, str, str, datetime, float | None, str]


class AnalyticsBackend(Protocol):
    """The minimal surface the platform uses; any warehouse connector implements this."""

    def insert_exposures(self, rows: Sequence[ExposureRow]) -> None: ...

    def insert_events(self, rows: Sequence[EventRow]) -> None: ...

    def exposure_counts(self, workspace_id: str, experiment_key: str) -> dict[str, int]:
        """Distinct exposed units per variant (used for SRM)."""
        ...

    def proportion_stats(
        self, workspace_id: str, experiment_key: str, event_name: str
    ) -> dict[str, tuple[int, int]]:
        """Per variant: (n exposed units, successes = units with >=1 ``event_name``)."""
        ...

    def continuous_stats(
        self, workspace_id: str, experiment_key: str, event_name: str, *, use_value: bool
    ) -> dict[str, tuple[int, float, float]]:
        """Per variant: (n, sum, sum-of-squares) of a per-unit metric."""
        ...

    def close(self) -> None: ...
