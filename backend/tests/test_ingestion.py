"""Ingestion: workspace allow-list, PII guard (no PII reaches storage), idempotency."""

from __future__ import annotations

import uuid

from app.analytics.store import DuckStore
from app.ingestion import ingest_events
from app.schemas.events import EventIn, EventsRequest, ExposureIn
from fastapi.testclient import TestClient

WS = uuid.uuid4()


def _count(store: DuckStore, table: str) -> int:
    row = store.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def test_allow_list_rejects_unknown_event(store: DuckStore) -> None:
    payload = EventsRequest(events=[EventIn(unit_id="u1", name="signup")])
    result = ingest_events(store, WS, {"events": ["purchase"]}, payload)
    assert result.accepted == 0
    assert result.rejected[0].reason.startswith("event 'signup'")
    assert _count(store, "events") == 0


def test_allow_list_rejects_unlisted_prop(store: DuckStore) -> None:
    payload = EventsRequest(events=[EventIn(unit_id="u1", name="purchase", props={"secret": "x"})])
    result = ingest_events(store, WS, {"events": {"purchase": ["sku_count"]}}, payload)
    assert result.accepted == 0
    assert "not allowed" in result.rejected[0].reason


def test_pii_rejected_and_not_stored(store: DuckStore) -> None:
    payload = EventsRequest(
        events=[
            EventIn(unit_id="u1", name="purchase", props={"email": "a@b.com"}),
            EventIn(unit_id="a@b.com", name="purchase"),
        ]
    )
    result = ingest_events(store, WS, {}, payload)
    assert result.accepted == 0
    assert len(result.rejected) == 2
    assert _count(store, "events") == 0  # no PII reached storage


def test_idempotent_on_event_id(store: DuckStore) -> None:
    event = EventIn(unit_id="u1", name="purchase", event_id="e1")
    ingest_events(store, WS, {}, EventsRequest(events=[event]))
    ingest_events(store, WS, {}, EventsRequest(events=[event]))
    assert _count(store, "events") == 1


def test_accepts_valid_events_and_exposures(store: DuckStore) -> None:
    payload = EventsRequest(
        events=[EventIn(unit_id="u1", name="purchase", value=9.99, props={"sku_count": 2})],
        exposures=[ExposureIn(experiment_key="checkout", variant_key="control", unit_id="u1")],
    )
    result = ingest_events(store, WS, {}, payload)
    assert result.accepted == 2
    assert _count(store, "events") == 1
    assert _count(store, "exposures") == 1


def test_events_endpoint_accepts(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.post(
        "/v1/events",
        json={
            "events": [{"unit_id": "u1", "name": "purchase", "value": 5.0}],
            "exposures": [{"experiment_key": "x", "variant_key": "control", "unit_id": "u1"}],
        },
        headers={"X-Workspace-Id": tenant["workspace_id"]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["accepted"] == 2


def test_events_endpoint_rejects_pii(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.post(
        "/v1/events",
        json={"events": [{"unit_id": "u1", "name": "purchase", "props": {"email": "a@b.com"}}]},
        headers={"X-Workspace-Id": tenant["workspace_id"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == 0
    assert body["rejected"][0]["kind"] == "event"
