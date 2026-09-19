"""SqlStore: a warehouse connector implementing ``AnalyticsBackend`` over SQLAlchemy.

The same sufficient-statistics queries as ``DuckStore``, issued through a SQLAlchemy engine, so
the analysis pipeline runs unchanged against any SQL warehouse that has a SQLAlchemy dialect
(Postgres today; Snowflake / BigQuery / Databricks with the matching driver installed). Tested
against SQLite. Reads return only aggregates — never raw rows.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.analytics.base import EventRow, ExposureRow
from app.core.db import make_engine

_EXPOSURE_COLS = (
    "exposure_id",
    "workspace_id",
    "experiment_key",
    "variant_key",
    "unit_id",
    "ts",
    "attrs",
)
_EVENT_COLS = ("event_id", "workspace_id", "unit_id", "name", "ts", "value", "props")


def _to_params(cols: tuple[str, ...], rows: Sequence[tuple[Any, ...]]) -> list[dict[str, Any]]:
    """Map positional rows to bind dicts; render datetimes as ISO strings (portable)."""
    params: list[dict[str, Any]] = []
    for row in rows:
        record = dict(zip(cols, row, strict=True))
        ts = record.get("ts")
        if isinstance(ts, datetime):
            record["ts"] = ts.isoformat()
        params.append(record)
    return params


class SqlStore:
    """``AnalyticsBackend`` backed by a SQL database/warehouse via SQLAlchemy."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._init_schema()

    @classmethod
    def from_url(cls, url: str) -> SqlStore:
        return cls(make_engine(url))

    def _init_schema(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS exposures ("
                    "exposure_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, "
                    "experiment_key TEXT NOT NULL, variant_key TEXT NOT NULL, "
                    "unit_id TEXT NOT NULL, ts TIMESTAMP NOT NULL, "
                    "attrs TEXT NOT NULL DEFAULT '{}')"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS events ("
                    "event_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, unit_id TEXT NOT NULL, "
                    "name TEXT NOT NULL, ts TIMESTAMP NOT NULL, value DOUBLE PRECISION, "
                    "props TEXT NOT NULL DEFAULT '{}')"
                )
            )

    # ---- writes (idempotent on the primary key) ----
    def insert_exposures(self, rows: Sequence[ExposureRow]) -> None:
        if not rows:
            return
        params = _to_params(_EXPOSURE_COLS, rows)
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO exposures "
                    "(exposure_id, workspace_id, experiment_key, variant_key, unit_id, ts, attrs) "
                    "VALUES (:exposure_id, :workspace_id, :experiment_key, :variant_key, "
                    ":unit_id, :ts, :attrs) ON CONFLICT (exposure_id) DO NOTHING"
                ),
                params,
            )

    def insert_events(self, rows: Sequence[EventRow]) -> None:
        if not rows:
            return
        params = _to_params(_EVENT_COLS, rows)
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO events (event_id, workspace_id, unit_id, name, ts, value, props) "
                    "VALUES (:event_id, :workspace_id, :unit_id, :name, :ts, :value, :props) "
                    "ON CONFLICT (event_id) DO NOTHING"
                ),
                params,
            )

    # ---- sufficient statistics ----
    def exposure_counts(self, workspace_id: str, experiment_key: str) -> dict[str, int]:
        sql = text(
            "SELECT variant_key, COUNT(DISTINCT unit_id) FROM exposures "
            "WHERE workspace_id = :ws AND experiment_key = :ek GROUP BY variant_key"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"ws": workspace_id, "ek": experiment_key}).fetchall()
        return {str(row[0]): int(row[1]) for row in rows}

    def proportion_stats(
        self, workspace_id: str, experiment_key: str, event_name: str
    ) -> dict[str, tuple[int, int]]:
        sql = text(
            """
            WITH exposed AS (
                SELECT DISTINCT variant_key, unit_id FROM exposures
                WHERE workspace_id = :ws AND experiment_key = :ek
            ),
            converted AS (
                SELECT DISTINCT unit_id FROM events WHERE workspace_id = :ws AND name = :ev
            )
            SELECT e.variant_key, COUNT(*) AS n, COUNT(c.unit_id) AS successes
            FROM exposed e LEFT JOIN converted c ON e.unit_id = c.unit_id
            GROUP BY e.variant_key
            """
        )
        params = {"ws": workspace_id, "ek": experiment_key, "ev": event_name}
        with self._engine.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return {str(row[0]): (int(row[1]), int(row[2])) for row in rows}

    def continuous_stats(
        self, workspace_id: str, experiment_key: str, event_name: str, *, use_value: bool
    ) -> dict[str, tuple[int, float, float]]:
        metric = "agg.total_value" if use_value else "agg.event_count"
        sql = text(
            f"""
            WITH exposed AS (
                SELECT DISTINCT variant_key, unit_id FROM exposures
                WHERE workspace_id = :ws AND experiment_key = :ek
            ),
            agg AS (
                SELECT unit_id, SUM(value) AS total_value, COUNT(*) AS event_count
                FROM events WHERE workspace_id = :ws AND name = :ev GROUP BY unit_id
            ),
            per_unit AS (
                SELECT e.variant_key, COALESCE({metric}, 0) AS x
                FROM exposed e LEFT JOIN agg ON e.unit_id = agg.unit_id
            )
            SELECT variant_key, COUNT(*), SUM(x), SUM(x * x) FROM per_unit GROUP BY variant_key
            """
        )
        params = {"ws": workspace_id, "ek": experiment_key, "ev": event_name}
        with self._engine.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return {
            str(row[0]): (int(row[1]), float(row[2] or 0.0), float(row[3] or 0.0)) for row in rows
        }

    def close(self) -> None:
        self._engine.dispose()
