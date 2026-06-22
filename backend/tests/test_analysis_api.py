"""End-to-end analysis: create -> seed events -> analyze -> results (+ SRM, power)."""

from __future__ import annotations

from app.analytics.store import DuckStore
from app.analytics.synthetic import SyntheticSpec, generate_conversions
from fastapi.testclient import TestClient


def _setup(client: TestClient, tenant: dict[str, str]) -> dict[str, str]:
    h = {"X-Workspace-Id": tenant["workspace_id"]}
    metric = client.post(
        "/v1/metrics",
        json={
            "key": "conv",
            "name": "Conversion",
            "type": "proportion",
            "numerator": {"event": "purchase"},
        },
        headers=h,
    ).json()
    client.post(
        "/v1/experiments",
        json={
            "key": "checkout",
            "name": "Checkout",
            "variants": [
                {"key": "control", "is_control": True, "allocation_pct": 50},
                {"key": "treatment", "is_control": False, "allocation_pct": 50},
            ],
        },
        headers=h,
    )
    client.post(
        "/v1/experiments/checkout/metrics",
        json={"metric_id": metric["id"], "role": "primary", "is_oec": True},
        headers=h,
    )
    client.post("/v1/experiments/checkout/transition", json={"status": "review"}, headers=h)
    client.post("/v1/experiments/checkout/transition", json={"status": "running"}, headers=h)
    return h


def test_analyze_recovers_effect(
    client: TestClient, tenant: dict[str, str], store: DuckStore
) -> None:
    h = _setup(client, tenant)
    generate_conversions(
        store,
        SyntheticSpec(
            workspace_id=tenant["workspace_id"], experiment_key="checkout", n=4000, seed=3
        ),
        control_rate=0.10,
        treatment_rate=0.16,
    )
    resp = client.post("/v1/experiments/checkout/analyze", json={}, headers=h)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["srm"] is not None and body["srm"]["is_mismatch"] is False

    treatment = next(r for r in body["results"] if r["variant_key"] == "treatment")
    assert treatment["abs_effect"] > 0
    assert treatment["is_significant"]
    assert treatment["rel_effect"] > 0.3  # ~16% vs 10% -> +60% lift
    assert treatment["prob_to_beat_control"] > 0.99  # Bayesian agrees
    assert treatment["expected_loss"] < 1e-3

    latest = client.get("/v1/experiments/checkout/results", headers=h)
    assert latest.status_code == 200
    assert latest.json()["id"] == body["id"]


def test_analyze_flags_srm(client: TestClient, tenant: dict[str, str], store: DuckStore) -> None:
    h = _setup(client, tenant)
    generate_conversions(
        store,
        SyntheticSpec(
            workspace_id=tenant["workspace_id"],
            experiment_key="checkout",
            n=4000,
            seed=5,
            control_fraction=0.65,  # intended 50/50 -> mismatch
        ),
        control_rate=0.10,
        treatment_rate=0.10,
    )
    body = client.post("/v1/experiments/checkout/analyze", json={}, headers=h).json()
    assert body["srm"]["is_mismatch"] is True


def test_results_404_before_analysis(client: TestClient, tenant: dict[str, str]) -> None:
    h = {"X-Workspace-Id": tenant["workspace_id"]}
    client.post(
        "/v1/experiments",
        json={
            "key": "x",
            "name": "x",
            "variants": [{"key": "control", "is_control": True, "allocation_pct": 100}],
        },
        headers=h,
    )
    assert client.get("/v1/experiments/x/results", headers=h).status_code == 404


def test_power_endpoint(client: TestClient, tenant: dict[str, str]) -> None:
    h = {"X-Workspace-Id": tenant["workspace_id"]}
    client.post(
        "/v1/experiments",
        json={
            "key": "x",
            "name": "x",
            "variants": [{"key": "control", "is_control": True, "allocation_pct": 100}],
        },
        headers=h,
    )
    resp = client.get("/v1/experiments/x/power?baseline=0.1&mde=0.02&daily_traffic=1000", headers=h)
    assert resp.status_code == 200
    body = resp.json()
    assert body["sample_size_per_arm"] > 0
    assert body["runtime_days"] is not None
