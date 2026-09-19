"""SSO bearer-token auth: HS256 JWT verification + role mapping in get_tenant."""

from __future__ import annotations

import uuid

import pytest
from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.jwt import decode_hs256, encode_hs256
from fastapi.testclient import TestClient

_SECRET = "s3cr3t-test"


# ---- the verifier (unit) ----
def test_jwt_roundtrip() -> None:
    token = encode_hs256({"sub": "u1", "role": "admin"}, _SECRET)
    assert decode_hs256(token, _SECRET) == {"sub": "u1", "role": "admin"}


def test_jwt_bad_signature_rejected() -> None:
    token = encode_hs256({"role": "editor"}, _SECRET)
    with pytest.raises(UnauthorizedError):
        decode_hs256(token, "a-different-secret")


def test_jwt_expired_rejected() -> None:
    token = encode_hs256({"role": "editor", "exp": 0}, _SECRET)  # 1970
    with pytest.raises(UnauthorizedError):
        decode_hs256(token, _SECRET)


# ---- the auth path (endpoint) ----
def _payload(key: str = "checkout") -> dict[str, object]:
    return {
        "key": key,
        "name": key,
        "variants": [
            {"key": "control", "is_control": True, "allocation_pct": 50},
            {"key": "treatment", "is_control": False, "allocation_pct": 50},
        ],
    }


def _bearer(token: str, workspace_id: str) -> dict[str, str]:
    return {"X-Workspace-Id": workspace_id, "Authorization": f"Bearer {token}"}


def _enable_sso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SSO_JWT_SECRET", _SECRET)
    get_settings.cache_clear()


def test_sso_bearer_editor_can_write(
    client: TestClient, tenant: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_sso(monkeypatch)
    token = encode_hs256({"org": tenant["org_id"], "role": "editor"}, _SECRET)
    resp = client.post(
        "/v1/experiments", json=_payload(), headers=_bearer(token, tenant["workspace_id"])
    )
    assert resp.status_code == 201
    get_settings.cache_clear()


def test_sso_bearer_viewer_forbidden_on_write(
    client: TestClient, tenant: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_sso(monkeypatch)
    token = encode_hs256({"org": tenant["org_id"], "role": "viewer"}, _SECRET)
    resp = client.post(
        "/v1/experiments", json=_payload(), headers=_bearer(token, tenant["workspace_id"])
    )
    assert resp.status_code == 403
    get_settings.cache_clear()


def test_sso_bad_signature_is_401(
    client: TestClient, tenant: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_sso(monkeypatch)
    forged = encode_hs256({"org": tenant["org_id"], "role": "admin"}, "wrong-secret")
    resp = client.get("/v1/experiments", headers=_bearer(forged, tenant["workspace_id"]))
    assert resp.status_code == 401
    get_settings.cache_clear()


def test_sso_org_mismatch_is_401(
    client: TestClient, tenant: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_sso(monkeypatch)
    token = encode_hs256({"org": str(uuid.uuid4()), "role": "editor"}, _SECRET)
    resp = client.get("/v1/experiments", headers=_bearer(token, tenant["workspace_id"]))
    assert resp.status_code == 401
    get_settings.cache_clear()
