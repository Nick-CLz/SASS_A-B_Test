"""SaaS hardening (P15): RBAC, tenant isolation, audit log, and API keys."""

from __future__ import annotations

from app.models import Organization, Workspace
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session


def _payload(key: str = "checkout") -> dict[str, object]:
    return {
        "key": key,
        "name": key,
        "variants": [
            {"key": "control", "is_control": True, "allocation_pct": 50},
            {"key": "treatment", "is_control": False, "allocation_pct": 50},
        ],
    }


def _headers(
    tenant: dict[str, str], *, role: str | None = None, api_key: str | None = None
) -> dict[str, str]:
    headers = {"X-Workspace-Id": tenant["workspace_id"]}
    if role is not None:
        headers["X-Role"] = role
    if api_key is not None:
        headers["X-Api-Key"] = api_key
    return headers


# ---- RBAC ----
def test_viewer_cannot_create_experiment(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.post("/v1/experiments", json=_payload(), headers=_headers(tenant, role="viewer"))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_editor_can_create_experiment(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.post("/v1/experiments", json=_payload(), headers=_headers(tenant, role="editor"))
    assert resp.status_code == 201


def test_viewer_can_read(client: TestClient, tenant: dict[str, str]) -> None:
    client.post("/v1/experiments", json=_payload(), headers=_headers(tenant))
    assert client.get("/v1/experiments", headers=_headers(tenant, role="viewer")).status_code == 200


# ---- tenant isolation ----
def test_tenant_isolation(
    client: TestClient, tenant: dict[str, str], migrated_engine: Engine
) -> None:
    client.post("/v1/experiments", json=_payload(key="secret"), headers=_headers(tenant))
    with Session(migrated_engine) as session:
        org_b = Organization(name="B", slug="org-b")
        session.add(org_b)
        session.commit()
        session.refresh(org_b)
        ws_b = Workspace(org_id=org_b.id, name="B", slug="ws-b")
        session.add(ws_b)
        session.commit()
        session.refresh(ws_b)
        ws_b_id = str(ws_b.id)

    other = {"X-Workspace-Id": ws_b_id}
    assert client.get("/v1/experiments/secret", headers=other).status_code == 404
    assert client.get("/v1/experiments", headers=other).json() == []


# ---- audit ----
def test_audit_records_sensitive_actions(client: TestClient, tenant: dict[str, str]) -> None:
    h = _headers(tenant)
    client.post("/v1/experiments", json=_payload(), headers=h)
    client.post("/v1/experiments/checkout/transition", json={"status": "review"}, headers=h)
    actions = [entry["action"] for entry in client.get("/v1/audit", headers=h).json()]
    assert "experiment.create" in actions
    assert "experiment.transition" in actions


def test_audit_requires_admin(client: TestClient, tenant: dict[str, str]) -> None:
    assert client.get("/v1/audit", headers=_headers(tenant, role="editor")).status_code == 403


# ---- API keys ----
def test_api_key_create_list_and_auth(client: TestClient, tenant: dict[str, str]) -> None:
    created = client.post(
        "/v1/api-keys",
        json={"name": "svc", "scopes": ["assign", "track"]},
        headers=_headers(tenant),
    )
    assert created.status_code == 201
    secret = created.json()["secret"]
    assert secret.startswith("mk_")

    listing = client.get("/v1/api-keys", headers=_headers(tenant)).json()
    assert len(listing) == 1
    assert "secret" not in listing[0]

    # the key (assign/track scope -> editor) can create an experiment
    used = client.post(
        "/v1/experiments", json=_payload(key="viakey"), headers=_headers(tenant, api_key=secret)
    )
    assert used.status_code == 201


def test_invalid_api_key_is_rejected(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.get("/v1/experiments", headers=_headers(tenant, api_key="mk_bogus"))
    assert resp.status_code == 401
