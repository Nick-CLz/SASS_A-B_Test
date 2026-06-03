"""Seedable synthetic experiment data — the backbone of the stats tests and the demo.

Generates exposures (units split across variants) plus conversion or continuous events with
a *known* effect, an optional injected SRM (via skewed allocation), and an optional
pre-period covariate (for CUPED in P08). Deterministic given ``seed``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.analytics.store import DuckStore, EventRow, ExposureRow, new_id
from app.models.base import utcnow


@dataclass
class SyntheticSpec:
    workspace_id: str = "ws"
    experiment_key: str = "exp"
    event_name: str = "purchase"
    n: int = 2000
    seed: int = 0
    # control fraction of traffic; (0.5 = balanced; e.g. 0.6 injects an SRM)
    control_fraction: float = 0.5


def generate_conversions(
    store: DuckStore,
    spec: SyntheticSpec,
    *,
    control_rate: float = 0.10,
    treatment_rate: float = 0.12,
) -> dict[str, int]:
    """Bernoulli conversions with a known rate per arm. Returns exposed counts per arm."""
    rng = random.Random(spec.seed)
    ts = utcnow()
    exposures: list[ExposureRow] = []
    events: list[EventRow] = []
    counts = {"control": 0, "treatment": 0}
    for i in range(spec.n):
        unit = f"u{spec.seed}-{i}"
        variant = "control" if rng.random() < spec.control_fraction else "treatment"
        counts[variant] += 1
        exposures.append(
            (new_id(), spec.workspace_id, spec.experiment_key, variant, unit, ts, "{}")
        )
        rate = control_rate if variant == "control" else treatment_rate
        if rng.random() < rate:
            events.append((new_id(), spec.workspace_id, unit, spec.event_name, ts, 1.0, "{}"))
    store.insert_exposures(exposures)
    store.insert_events(events)
    return counts


def generate_continuous(
    store: DuckStore,
    spec: SyntheticSpec,
    *,
    control_mean: float = 10.0,
    treatment_mean: float = 11.0,
    sigma: float = 5.0,
) -> dict[str, int]:
    """One Normal-valued event per unit per arm. Returns exposed counts per arm."""
    rng = random.Random(spec.seed)
    ts = utcnow()
    exposures: list[ExposureRow] = []
    events: list[EventRow] = []
    counts = {"control": 0, "treatment": 0}
    for i in range(spec.n):
        unit = f"u{spec.seed}-{i}"
        variant = "control" if rng.random() < spec.control_fraction else "treatment"
        counts[variant] += 1
        exposures.append(
            (new_id(), spec.workspace_id, spec.experiment_key, variant, unit, ts, "{}")
        )
        mean = control_mean if variant == "control" else treatment_mean
        value = rng.gauss(mean, sigma)
        events.append((new_id(), spec.workspace_id, unit, spec.event_name, ts, value, "{}"))
    store.insert_exposures(exposures)
    store.insert_events(events)
    return counts
