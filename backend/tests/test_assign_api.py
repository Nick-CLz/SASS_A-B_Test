"""Assignment endpoint (/v1/assign) tests: caching, exposure, and lifecycle gating."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.api.deps import get_exposure_sink
from app.assignment.cache import clear
from app.assignment.exposure import InMemoryExposureSink
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolate_cache() -> Iterator[None]:
    clear()
    yield
    clear()


def _headers(tenant: dict[str, str]) -> dict[str, str]:
    return {"X-Workspace-Id": tenant["workspace_id"]}


def _run_experiment(client: TestClient, headers: dict[str, str], key: str = "checkout") -> None:
    client.post(
        "/v1/experiments",
        json={
            "key": key,
            "name": key,
            "variants": [
                {"key": "control", "is_control": True, "allocation_pct": 50},
                {"key": "treatment", "is_control": False, "allocation_pct": 50},
            ],
        },
        headers=headers,
    )
    client.post(f"/v1/experiments/{key}/transition", json={"status": "review"}, headers=headers)
    client.post(f"/v1/experiments/{key}/transition", json={"status": "running"}, headers=headers)


def test_assign_single_experiment_is_deterministic(
    client: TestClient, tenant: dict[str, str]
) -> None:
    h = _headers(tenant)
    _run_experiment(client, h)
    resp = client.post(
        "/v1/assign", json={"unit_id": "user-1", "experiment_key": "checkout"}, headers=h
    )
    assert resp.status_code == 200, resp.text
    assignments = resp.json()["assignments"]
    assert len(assignments) == 1
    first = assignments[0]
    assert first["experiment_key"] == "checkout"
    assert first["in_experiment"] is True
    assert first["variant_key"] in {"control", "treatment"}

    again = client.post(
        "/v1/assign", json={"unit_id": "user-1", "experiment_key": "checkout"}, headers=h
    )
    assert again.json()["assignments"][0]["variant_key"] == first["variant_key"]


def test_assign_all_running(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    _run_experiment(client, h, "checkout")
    _run_experiment(client, h, "banner")
    resp = client.post("/v1/assign", json={"unit_id": "user-1"}, headers=h)
    keys = {a["experiment_key"] for a in resp.json()["assignments"]}
    assert keys == {"checkout", "banner"}


def test_unknown_experiment_404(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.post(
        "/v1/assign", json={"unit_id": "user-1", "experiment_key": "nope"}, headers=_headers(tenant)
    )
    assert resp.status_code == 404


def test_draft_experiment_not_assignable(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    client.post(
        "/v1/experiments",
        json={
            "key": "draft1",
            "name": "draft1",
            "variants": [{"key": "control", "is_control": True, "allocation_pct": 100}],
        },
        headers=h,
    )
    assert (
        client.post("/v1/assign", json={"unit_id": "user-1"}, headers=h).json()["assignments"] == []
    )
    specific = client.post(
        "/v1/assign", json={"unit_id": "user-1", "experiment_key": "draft1"}, headers=h
    )
    assert specific.status_code == 404


def test_cache_invalidated_when_experiment_starts(
    client: TestClient, tenant: dict[str, str]
) -> None:
    h = _headers(tenant)
    # First call caches an empty running-set for this workspace.
    assert (
        client.post("/v1/assign", json={"unit_id": "user-1"}, headers=h).json()["assignments"] == []
    )
    # Starting an experiment must invalidate that cache.
    _run_experiment(client, h, "checkout")
    assert (
        len(client.post("/v1/assign", json={"unit_id": "user-1"}, headers=h).json()["assignments"])
        == 1
    )


def test_exposure_is_logged(client: TestClient, tenant: dict[str, str]) -> None:
    sink = InMemoryExposureSink()
    app.dependency_overrides[get_exposure_sink] = lambda: sink
    h = _headers(tenant)
    _run_experiment(client, h)
    client.post("/v1/assign", json={"unit_id": "user-1", "experiment_key": "checkout"}, headers=h)
    assert len(sink.events) == 1
    assert sink.events[0].experiment_key == "checkout"
    assert sink.events[0].unit_id == "user-1"
