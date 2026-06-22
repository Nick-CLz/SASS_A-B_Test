"""Assignment engine: correctness-critical tests (see docs/04-statistics-engine.md)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
from app.assignment import (
    Assignment,
    ExperimentSpec,
    LayerSlot,
    VariantSpec,
    assign,
    bucket,
    evaluate_targeting,
)
from scipy import stats

FIXTURE = json.loads(
    (Path(__file__).resolve().parents[2] / "sdks" / "fixtures" / "bucketing.json").read_text()
)


# --------------------------------------------------------------- cross-language contract
def test_golden_buckets() -> None:
    for case in FIXTURE["bucket"]:
        assert bucket(case["salt"], case["unit_id"]) == case["bucket"]


def test_golden_assignments() -> None:
    spec_data = FIXTURE["assignment_spec"]
    spec = ExperimentSpec(
        key=spec_data["key"],
        salt=spec_data["salt"],
        variants=tuple(VariantSpec(v["key"], v["allocation_pct"]) for v in spec_data["variants"]),
    )
    for case in FIXTURE["assignment"]:
        assert assign(spec, case["unit_id"]).variant_key == case["variant_key"]


# --------------------------------------------------------------------------- properties
def test_determinism() -> None:
    spec = ExperimentSpec("e", "e", (VariantSpec("c", 50), VariantSpec("t", 50)))
    first = assign(spec, "user-42")
    for _ in range(100):
        assert assign(spec, "user-42") == first


def test_bucket_in_unit_interval() -> None:
    for i in range(1000):
        value = bucket("e", f"u{i}")
        assert 0.0 <= value < 1.0


def test_uniformity_ks() -> None:
    xs = np.array([bucket("checkout", f"u{i}") for i in range(20000)])
    assert float(stats.kstest(xs, "uniform").pvalue) > 0.05


def test_split_proportions() -> None:
    spec = ExperimentSpec("e", "e", (VariantSpec("control", 70), VariantSpec("treatment", 30)))
    counts = Counter(assign(spec, f"u{i}").variant_key for i in range(50000))
    assert abs(counts["control"] / 50000 - 0.70) < 0.02
    assert abs(counts["treatment"] / 50000 - 0.30) < 0.02


def test_traffic_allocation_gate() -> None:
    spec = ExperimentSpec("e", "e", (VariantSpec("c", 50), VariantSpec("t", 50)), traffic_pct=10.0)
    in_exp = sum(assign(spec, f"u{i}").in_experiment for i in range(50000))
    assert abs(in_exp / 50000 - 0.10) < 0.02


def test_orthogonality_across_salts() -> None:
    a = ExperimentSpec("a", "salt-a", (VariantSpec("c", 50), VariantSpec("t", 50)))
    b = ExperimentSpec("b", "salt-b", (VariantSpec("c", 50), VariantSpec("t", 50)))
    n = 40000
    joint = Counter(
        (assign(a, f"u{i}").variant_key, assign(b, f"u{i}").variant_key) for i in range(n)
    )
    # independent 50/50 x 50/50 => each of the 4 cells ~ 25%
    for cell in (("c", "c"), ("c", "t"), ("t", "c"), ("t", "t")):
        assert abs(joint[cell] / n - 0.25) < 0.02


def test_layer_mutual_exclusion() -> None:
    x = ExperimentSpec(
        "x",
        "x",
        (VariantSpec("c", 50), VariantSpec("t", 50)),
        layer=LayerSlot("layer-1", 0.0, 0.5),
    )
    y = ExperimentSpec(
        "y",
        "y",
        (VariantSpec("c", 50), VariantSpec("t", 50)),
        layer=LayerSlot("layer-1", 0.5, 1.0),
    )
    in_x = in_y = both = 0
    for i in range(40000):
        ax = assign(x, f"u{i}").in_experiment
        ay = assign(y, f"u{i}").in_experiment
        in_x += ax
        in_y += ay
        both += ax and ay
    assert both == 0  # mutually exclusive within the layer
    assert abs(in_x / 40000 - 0.5) < 0.02
    assert abs(in_y / 40000 - 0.5) < 0.02


def test_layer_holdout_range() -> None:
    # X in [0,0.4), Y in [0.4,0.8); [0.8,1.0) is an uncovered holdout.
    x = ExperimentSpec("x", "x", (VariantSpec("c", 100),), layer=LayerSlot("L", 0.0, 0.4))
    y = ExperimentSpec("y", "y", (VariantSpec("c", 100),), layer=LayerSlot("L", 0.4, 0.8))
    holdout = sum(
        not assign(x, f"u{i}").in_experiment and not assign(y, f"u{i}").in_experiment
        for i in range(40000)
    )
    assert abs(holdout / 40000 - 0.20) < 0.02


# --------------------------------------------------------------------------- targeting
def test_targeting_operators() -> None:
    rules = {"match": "all", "rules": [{"attribute": "country", "operator": "in", "value": ["US"]}]}
    assert evaluate_targeting({"country": "US"}, rules) is True
    assert evaluate_targeting({"country": "CA"}, rules) is False
    assert evaluate_targeting({}, rules) is False  # missing attribute
    assert evaluate_targeting({}, {}) is True  # no rules => eligible


def test_targeting_match_any() -> None:
    rules = {
        "match": "any",
        "rules": [
            {"attribute": "plan", "operator": "eq", "value": "pro"},
            {"attribute": "beta", "operator": "exists"},
        ],
    }
    assert evaluate_targeting({"plan": "free", "beta": True}, rules) is True
    assert evaluate_targeting({"plan": "free"}, rules) is False


def test_ineligible_unit_not_counted() -> None:
    spec = ExperimentSpec(
        "e",
        "e",
        (VariantSpec("c", 100),),
        targeting={"rules": [{"attribute": "country", "operator": "eq", "value": "US"}]},
    )
    result: Assignment = assign(spec, "user-1", {"country": "CA"})
    assert result.eligible is False
    assert result.in_experiment is False
    assert result.variant_key is None
