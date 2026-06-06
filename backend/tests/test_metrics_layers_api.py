"""Metric + layer API tests, including attaching a metric to an experiment."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(tenant: dict[str, str]) -> dict[str, str]:
    return {"X-Workspace-Id": tenant["workspace_id"]}


def test_metric_crud_and_duplicate(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    resp = client.post(
        "/v1/metrics", json={"key": "conv", "name": "Conversion", "type": "proportion"}, headers=h
    )
    assert resp.status_code == 201
    listing = client.get("/v1/metrics", headers=h)
    assert listing.status_code == 200
    assert listing.json()[0]["key"] == "conv"

    dup = client.post("/v1/metrics", json={"key": "conv", "name": "Dup", "type": "mean"}, headers=h)
    assert dup.status_code == 409


def test_attach_metric_to_experiment(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    metric = client.post(
        "/v1/metrics", json={"key": "conv", "name": "Conversion", "type": "proportion"}, headers=h
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
    attach = client.post(
        "/v1/experiments/checkout/metrics",
        json={"metric_id": metric["id"], "role": "primary", "is_oec": True},
        headers=h,
    )
    assert attach.status_code == 201, attach.text
    assert attach.json()["role"] == "primary"

    got = client.get("/v1/experiments/checkout", headers=h).json()
    assert len(got["metrics"]) == 1
    assert got["metrics"][0]["is_oec"] is True


def test_layer_crud(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    resp = client.post("/v1/layers", json={"name": "checkout-layer"}, headers=h)
    assert resp.status_code == 201
    listing = client.get("/v1/layers", headers=h)
    assert listing.json()[0]["name"] == "checkout-layer"
