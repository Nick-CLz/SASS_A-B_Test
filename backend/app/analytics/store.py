"""DuckDB analytics store: append-only event data + sufficient-statistics queries.

This is the default ``AnalyticsBackend`` (see docs/02-architecture.md). It holds the
exposure + event tables and returns **only sufficient statistics** (counts, sums,
sums-of-squares) — never raw rows — so the stats engine stays pure and the same queries
port to a warehouse later. No PII reaches here (the ingestion guard enforces that).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence
from datetime import datetime

import duckdb

ExposureRow = tuple[str, str, str, str, str, datetime, str]
EventRow = tuple[str, str, str, str, datetime, float | None, str]


class DuckStore:
    """Embedded analytics store. Use ``":memory:"`` (default) or a file path."""

    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        self.conn = duckdb.connect(path)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exposures (
                exposure_id   VARCHAR PRIMARY KEY,
                workspace_id  VARCHAR NOT NULL,
                experiment_key VARCHAR NOT NULL,
                variant_key   VARCHAR NOT NULL,
                unit_id       VARCHAR NOT NULL,
                ts            TIMESTAMP NOT NULL,
                attrs         VARCHAR NOT NULL DEFAULT '{}'
            );
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id      VARCHAR PRIMARY KEY,
                workspace_id  VARCHAR NOT NULL,
                unit_id       VARCHAR NOT NULL,
                name          VARCHAR NOT NULL,
                ts            TIMESTAMP NOT NULL,
                value         DOUBLE,
                props         VARCHAR NOT NULL DEFAULT '{}'
            );
            """
        )

    # ---- writes (idempotent on the primary key) ----
    def insert_exposures(self, rows: Sequence[ExposureRow]) -> None:
        if not rows:
            return
        self.conn.executemany(
            "INSERT OR IGNORE INTO exposures "
            "(exposure_id, workspace_id, experiment_key, variant_key, unit_id, ts, attrs) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            list(rows),
        )

    def insert_events(self, rows: Sequence[EventRow]) -> None:
        if not rows:
            return
        self.conn.executemany(
            "INSERT OR IGNORE INTO events "
            "(event_id, workspace_id, unit_id, name, ts, value, props) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            list(rows),
        )

    # ---- sufficient statistics (the only thing the stats engine consumes) ----
    def exposure_counts(self, workspace_id: str, experiment_key: str) -> dict[str, int]:
        """Distinct exposed units per variant (used for SRM)."""
        rows = self.conn.execute(
            "SELECT variant_key, COUNT(DISTINCT unit_id) "
            "FROM exposures WHERE workspace_id = ? AND experiment_key = ? GROUP BY variant_key",
            [workspace_id, experiment_key],
        ).fetchall()
        return {str(variant): int(n) for variant, n in rows}

    def proportion_stats(
        self, workspace_id: str, experiment_key: str, event_name: str
    ) -> dict[str, tuple[int, int]]:
        """Per variant: (n exposed units, successes = exposed units with >=1 ``event_name``)."""
        rows = self.conn.execute(
            """
            WITH exposed AS (
                SELECT DISTINCT variant_key, unit_id
                FROM exposures WHERE workspace_id = ? AND experiment_key = ?
            ),
            converted AS (
                SELECT DISTINCT unit_id FROM events WHERE workspace_id = ? AND name = ?
            )
            SELECT e.variant_key, COUNT(*) AS n, COUNT(c.unit_id) AS successes
            FROM exposed e LEFT JOIN converted c ON e.unit_id = c.unit_id
            GROUP BY e.variant_key
            """,
            [workspace_id, experiment_key, workspace_id, event_name],
        ).fetchall()
        return {str(v): (int(n), int(s)) for v, n, s in rows}

    def continuous_stats(
        self, workspace_id: str, experiment_key: str, event_name: str, *, use_value: bool
    ) -> dict[str, tuple[int, float, float]]:
        """Per variant: (n, sum, sum-of-squares) of a per-unit metric.

        ``use_value=True`` sums ``event.value`` per unit; ``False`` counts events per unit.
        Non-firing exposed units contribute 0 (avoids dilution bias).
        """
        metric = "agg.total_value" if use_value else "agg.event_count"
        rows = self.conn.execute(
            f"""
            WITH exposed AS (
                SELECT DISTINCT variant_key, unit_id
                FROM exposures WHERE workspace_id = ? AND experiment_key = ?
            ),
            agg AS (
                SELECT unit_id, SUM(value) AS total_value, COUNT(*) AS event_count
                FROM events WHERE workspace_id = ? AND name = ? GROUP BY unit_id
            ),
            per_unit AS (
                SELECT e.variant_key, COALESCE({metric}, 0) AS x
                FROM exposed e LEFT JOIN agg ON e.unit_id = agg.unit_id
            )
            SELECT variant_key, COUNT(*), SUM(x), SUM(x * x) FROM per_unit GROUP BY variant_key
            """,
            [workspace_id, experiment_key, workspace_id, event_name],
        ).fetchall()
        return {str(v): (int(n), float(s or 0.0), float(sq or 0.0)) for v, n, s, sq in rows}

    def close(self) -> None:
        self.conn.close()


def new_id() -> str:
    """A fresh row id (used by ingestion when the client doesn't supply one)."""
    return str(uuid.uuid4())
