"""Experiment CRUD + lifecycle API tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def _headers(tenant: dict[str, str]) -> dict[str, str]:
    return {"X-Workspace-Id": tenant["workspace_id"]}


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "key": "checkout",
        "name": "Checkout",
        "variants": [
            {"key": "control", "is_control": True, "allocation_pct": 50},
            {"key": "treatment", "is_control": False, "allocation_pct": 50},
        ],
    }
    base.update(overrides)
    return base


def test_create_and_get(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.post("/v1/experiments", json=_payload(), headers=_headers(tenant))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["key"] == "checkout"
    assert body["status"] == "draft"
    assert body["salt"] == "checkout"  # defaulted from key
    assert len(body["variants"]) == 2

    got = client.get("/v1/experiments/checkout", headers=_headers(tenant))
    assert got.status_code == 200
    assert got.json()["key"] == "checkout"


def test_create_rejects_bad_allocations(client: TestClient, tenant: dict[str, str]) -> None:
    bad = _payload(
        variants=[
            {"key": "control", "is_control": True, "allocation_pct": 40},
            {"key": "t", "is_control": False, "allocation_pct": 40},
        ]
    )
    resp = client.post("/v1/experiments", json=bad, headers=_headers(tenant))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invariant_violation"


def test_duplicate_key_conflict(client: TestClient, tenant: dict[str, str]) -> None:
    client.post("/v1/experiments", json=_payload(), headers=_headers(tenant))
    resp = client.post("/v1/experiments", json=_payload(), headers=_headers(tenant))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_lifecycle_and_edit_lock(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    client.post("/v1/experiments", json=_payload(), headers=h)

    # draft -> running directly is not allowed
    bad = client.post("/v1/experiments/checkout/transition", json={"status": "running"}, headers=h)
    assert bad.status_code == 409
    assert bad.json()["error"]["code"] == "invalid_transition"

    # draft -> review -> running
    assert (
        client.post(
            "/v1/experiments/checkout/transition", json={"status": "review"}, headers=h
        ).status_code
        == 200
    )
    run = client.post("/v1/experiments/checkout/transition", json={"status": "running"}, headers=h)
    assert run.status_code == 200
    assert run.json()["status"] == "running"
    assert run.json()["start_at"] is not None

    # config is locked while running
    assert (
        client.patch("/v1/experiments/checkout", json={"name": "New"}, headers=h).status_code == 409
    )
    assert (
        client.post(
            "/v1/experiments/checkout/variants",
            json={"key": "t2", "allocation_pct": 0},
            headers=h,
        ).status_code
        == 409
    )


def test_running_requires_valid_variants(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    client.post("/v1/experiments", json={"key": "empty", "name": "Empty"}, headers=h)
    client.post("/v1/experiments/empty/transition", json={"status": "review"}, headers=h)
    resp = client.post("/v1/experiments/empty/transition", json={"status": "running"}, headers=h)
    assert resp.status_code == 422  # no variants -> invariant violation


def test_list_and_status_filter(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    client.post("/v1/experiments", json=_payload(), headers=h)
    client.post("/v1/experiments", json=_payload(key="other"), headers=h)
    assert len(client.get("/v1/experiments", headers=h).json()) == 2
    assert len(client.get("/v1/experiments?status=draft", headers=h).json()) == 2
    assert len(client.get("/v1/experiments?status=running", headers=h).json()) == 0


def test_unknown_workspace_404(client: TestClient) -> None:
    resp = client.get("/v1/experiments", headers={"X-Workspace-Id": str(uuid.uuid4())})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_missing_workspace_header_422(client: TestClient) -> None:
    assert client.get("/v1/experiments").status_code == 422
