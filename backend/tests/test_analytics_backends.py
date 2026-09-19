"""Analytics backend parity: SqlStore (SQLAlchemy) matches DuckStore on the same data.

Proves the AnalyticsBackend interface is real — the analysis pipeline runs unchanged on a SQL
warehouse. SqlStore is exercised against SQLite here; production uses a warehouse dialect.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.analytics.sql_store import SqlStore
from app.analytics.store import DuckStore
from app.analytics.synthetic import SyntheticSpec, generate_continuous, generate_conversions
from app.models.base import utcnow


def _spec(key: str) -> SyntheticSpec:
    return SyntheticSpec(workspace_id="ws", experiment_key=key, n=400, seed=7)


def test_proportion_stats_parity(tmp_path: Path) -> None:
    duck = DuckStore(":memory:")
    sql = SqlStore.from_url(f"sqlite:///{tmp_path}/p.db")
    spec = _spec("checkout")
    generate_conversions(duck, spec, control_rate=0.10, treatment_rate=0.16)
    generate_conversions(sql, spec, control_rate=0.10, treatment_rate=0.16)

    assert duck.exposure_counts("ws", "checkout") == sql.exposure_counts("ws", "checkout")
    assert duck.proportion_stats("ws", "checkout", "purchase") == sql.proportion_stats(
        "ws", "checkout", "purchase"
    )
    duck.close()
    sql.close()


def test_continuous_stats_parity(tmp_path: Path) -> None:
    duck = DuckStore(":memory:")
    sql = SqlStore.from_url(f"sqlite:///{tmp_path}/c.db")
    spec = _spec("revenue")
    generate_continuous(duck, spec, control_mean=10.0, treatment_mean=11.5)
    generate_continuous(sql, spec, control_mean=10.0, treatment_mean=11.5)

    d = duck.continuous_stats("ws", "revenue", "purchase", use_value=True)
    s = sql.continuous_stats("ws", "revenue", "purchase", use_value=True)
    assert d.keys() == s.keys()
    for variant in d:
        dn, dsum, dsq = d[variant]
        sn, ssum, ssq = s[variant]
        assert dn == sn
        assert dsum == pytest.approx(ssum, rel=1e-9)
        assert dsq == pytest.approx(ssq, rel=1e-9)
    duck.close()
    sql.close()


def test_sql_store_insert_is_idempotent(tmp_path: Path) -> None:
    sql = SqlStore.from_url(f"sqlite:///{tmp_path}/i.db")
    ts = utcnow()
    rows = [
        ("e1", "ws", "exp", "control", "u1", ts, "{}"),
        ("e2", "ws", "exp", "treatment", "u2", ts, "{}"),
    ]
    sql.insert_exposures(rows)
    sql.insert_exposures(rows)  # same primary keys → ignored, not duplicated
    assert sql.exposure_counts("ws", "exp") == {"control": 1, "treatment": 1}
    sql.close()
