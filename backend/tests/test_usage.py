"""Usage metering: per-org AI agent runs + tokens + analyses, admin-gated (GET /v1/usage)."""

from __future__ import annotations

import uuid

from app.models import Organization
from app.models.agent import AgentRun
from app.models.analysis import AnalysisRun
from app.models.enums import AgentRunStatus, AgentType
from app.services.repository import add
from app.services.usage import usage_summary
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session


def _run(org_id: uuid.UUID, agent_type: AgentType, tokens: int) -> AgentRun:
    return AgentRun(
        org_id=org_id,
        agent_type=agent_type,
        model="mock",
        status=AgentRunStatus.complete,
        cost_tokens=tokens,
    )


def test_usage_summary_counts_runs_and_tokens(session: Session) -> None:
    org = add(session, Organization(name="A", slug="a"))
    for agent_type, tokens in [
        (AgentType.analyst, 100),
        (AgentType.analyst, 50),
        (AgentType.monitor, 30),
    ]:
        session.add(_run(org.id, agent_type, tokens))
    session.commit()

    summary = usage_summary(session, org.id)
    assert summary.agent_runs == 3
    assert summary.agent_cost_tokens == 180
    assert summary.agent_runs_by_type == {"analyst": 2, "monitor": 1}
    assert summary.analyses == 0


def test_usage_summary_isolated_per_org(session: Session) -> None:
    a = add(session, Organization(name="A", slug="a"))
    b = add(session, Organization(name="B", slug="b"))
    session.add(_run(a.id, AgentType.designer, 10))
    session.commit()
    assert usage_summary(session, a.id).agent_runs == 1
    assert usage_summary(session, b.id).agent_runs == 0


def _experiment_payload() -> dict[str, object]:
    return {
        "key": "checkout",
        "name": "checkout",
        "variants": [
            {"key": "control", "is_control": True, "allocation_pct": 50},
            {"key": "treatment", "is_control": False, "allocation_pct": 50},
        ],
    }


def test_usage_endpoint_reports_org_usage(
    client: TestClient, tenant: dict[str, str], migrated_engine: Engine
) -> None:
    org_id = uuid.UUID(tenant["org_id"])
    headers = {"X-Workspace-Id": tenant["workspace_id"]}
    exp = client.post("/v1/experiments", json=_experiment_payload(), headers=headers).json()

    with Session(migrated_engine) as setup:
        setup.add(_run(org_id, AgentType.readout, 200))
        setup.add(AnalysisRun(org_id=org_id, experiment_id=uuid.UUID(exp["id"])))
        setup.commit()

    usage = client.get("/v1/usage", headers=headers).json()  # owner role by default → admin ok
    assert usage["agent_runs"] == 1
    assert usage["agent_cost_tokens"] == 200
    assert usage["agent_runs_by_type"] == {"readout": 1}
    assert usage["analyses"] == 1


def test_usage_requires_admin(client: TestClient, tenant: dict[str, str]) -> None:
    resp = client.get(
        "/v1/usage",
        headers={"X-Workspace-Id": tenant["workspace_id"], "X-Role": "editor"},
    )
    assert resp.status_code == 403
