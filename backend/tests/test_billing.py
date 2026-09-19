"""Billing: rate card × metered usage → priced invoice (admin-gated /v1/billing/invoice)."""

from __future__ import annotations

import uuid

import pytest
from app.models.agent import AgentRun
from app.models.analysis import AnalysisRun
from app.models.base import utcnow
from app.models.enums import AgentRunStatus, AgentType
from app.services.billing import RateCard, compute_invoice
from app.services.usage import UsageSummary
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session


def test_compute_invoice_prices_each_line() -> None:
    now = utcnow()
    usage = UsageSummary(
        org_id=uuid.uuid4(),
        period_start=now,
        period_end=now,
        agent_runs=10,
        agent_cost_tokens=5000,
        analyses=4,
    )
    invoice = compute_invoice(usage, RateCard())
    amounts = {line.description: line.amount for line in invoice.lines}
    assert amounts["AI agent runs"] == pytest.approx(1.00)  # 10 * 0.10
    assert amounts["Agent tokens (per 1k)"] == pytest.approx(0.05)  # 5 * 0.01
    assert amounts["Analyses"] == pytest.approx(0.20)  # 4 * 0.05
    assert invoice.total == pytest.approx(1.25)
    assert invoice.currency == "USD"


def _experiment_payload() -> dict[str, object]:
    return {
        "key": "checkout",
        "name": "checkout",
        "variants": [
            {"key": "control", "is_control": True, "allocation_pct": 50},
            {"key": "treatment", "is_control": False, "allocation_pct": 50},
        ],
    }


def test_billing_invoice_endpoint(
    client: TestClient, tenant: dict[str, str], migrated_engine: Engine
) -> None:
    org_id = uuid.UUID(tenant["org_id"])
    headers = {"X-Workspace-Id": tenant["workspace_id"]}
    exp = client.post("/v1/experiments", json=_experiment_payload(), headers=headers).json()

    with Session(migrated_engine) as setup:
        setup.add(
            AgentRun(
                org_id=org_id,
                agent_type=AgentType.analyst,
                model="mock",
                status=AgentRunStatus.complete,
                cost_tokens=1000,
            )
        )
        setup.add(AnalysisRun(org_id=org_id, experiment_id=uuid.UUID(exp["id"])))
        setup.commit()

    invoice = client.get("/v1/billing/invoice", headers=headers).json()
    # 1 run * 0.10 + (1000/1000) * 0.01 + 1 analysis * 0.05 = 0.16
    assert invoice["total"] == pytest.approx(0.16)
    assert invoice["currency"] == "USD"
    assert len(invoice["lines"]) == 3


def test_billing_requires_admin(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.get(
        "/v1/billing/invoice",
        headers={"X-Workspace-Id": tenant["workspace_id"], "X-Role": "editor"},
    )
    assert resp.status_code == 403
