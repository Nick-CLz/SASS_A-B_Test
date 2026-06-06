"""DuckDB-backed exposure sink: persists P04 assignment exposures to the analytics store."""

from __future__ import annotations

from app.analytics.store import DuckStore, new_id
from app.assignment.exposure import ExposureEvent
from app.models.base import utcnow


class DuckExposureSink:
    """Implements the ExposureSink protocol by writing exposures to the analytics store."""

    def __init__(self, store: DuckStore) -> None:
        self._store = store

    def log(self, event: ExposureEvent) -> None:
        self._store.insert_exposures(
            [
                (
                    new_id(),
                    event.workspace_id,
                    event.experiment_key,
                    event.variant_key,
                    event.unit_id,
                    utcnow(),
                    "{}",
                )
            ]
        )
