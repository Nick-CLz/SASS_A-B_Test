"""Parity with the server: reproduce the cross-language golden fixtures exactly."""

from __future__ import annotations

import json
from pathlib import Path

from mallard_sdk import ExperimentSpec, VariantSpec, assign, bucket

FIXTURE = json.loads(
    (Path(__file__).resolve().parents[2] / "fixtures" / "bucketing.json").read_text()
)


def test_bucket_parity() -> None:
    for case in FIXTURE["bucket"]:
        assert bucket(case["salt"], case["unit_id"]) == case["bucket"]


def test_assignment_parity() -> None:
    spec_data = FIXTURE["assignment_spec"]
    spec = ExperimentSpec(
        key=spec_data["key"],
        salt=spec_data["salt"],
        variants=tuple(VariantSpec(v["key"], v["allocation_pct"]) for v in spec_data["variants"]),
    )
    for case in FIXTURE["assignment"]:
        assert assign(spec, case["unit_id"]).variant_key == case["variant_key"]
