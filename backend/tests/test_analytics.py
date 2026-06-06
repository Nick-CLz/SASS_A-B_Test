"""Analytics adapter: sufficient statistics + the synthetic generator."""

from __future__ import annotations

from datetime import datetime

from app.analytics.store import DuckStore
from app.analytics.synthetic import SyntheticSpec, generate_conversions

WS = "ws-1"
TS = datetime(2026, 1, 1)  # noqa: DTZ001  (fixed timestamp for a deterministic fixture)


def _seed(store: DuckStore) -> None:
    # control: u1,u2,u3 (u1 converts) ; treatment: u4,u5 (both convert)
    store.insert_exposures(
        [
            ("e1", WS, "exp", "control", "u1", TS, "{}"),
            ("e2", WS, "exp", "control", "u2", TS, "{}"),
            ("e3", WS, "exp", "control", "u3", TS, "{}"),
            ("e4", WS, "exp", "treatment", "u4", TS, "{}"),
            ("e5", WS, "exp", "treatment", "u5", TS, "{}"),
        ]
    )
    store.insert_events(
        [
            ("ev1", WS, "u1", "purchase", TS, 1.0, "{}"),
            ("ev2", WS, "u4", "purchase", TS, 1.0, "{}"),
            ("ev3", WS, "u5", "purchase", TS, 1.0, "{}"),
        ]
    )


def test_exposure_counts(store: DuckStore) -> None:
    _seed(store)
    assert store.exposure_counts(WS, "exp") == {"control": 3, "treatment": 2}


def test_proportion_stats(store: DuckStore) -> None:
    _seed(store)
    stats = store.proportion_stats(WS, "exp", "purchase")
    assert stats["control"] == (3, 1)
    assert stats["treatment"] == (2, 2)


def test_continuous_stats_counts(store: DuckStore) -> None:
    _seed(store)
    stats = store.continuous_stats(WS, "exp", "purchase", use_value=False)
    assert stats["control"] == (3, 1.0, 1.0)  # values 1,0,0
    assert stats["treatment"] == (2, 2.0, 2.0)  # values 1,1


def test_distinct_exposures_not_inflated(store: DuckStore) -> None:
    _seed(store)
    store.insert_exposures([("e1b", WS, "exp", "control", "u1", TS, "{}")])  # dup unit
    assert store.exposure_counts(WS, "exp")["control"] == 3


def test_synthetic_recovers_planted_effect(store: DuckStore) -> None:
    spec = SyntheticSpec(workspace_id=WS, experiment_key="syn", n=4000, seed=7)
    generate_conversions(store, spec, control_rate=0.10, treatment_rate=0.20)
    stats = store.proportion_stats(WS, "syn", "purchase")
    c_n, c_s = stats["control"]
    t_n, t_s = stats["treatment"]
    assert t_s / t_n > c_s / c_n
    assert abs(c_s / c_n - 0.10) < 0.03
    assert abs(t_s / t_n - 0.20) < 0.03
