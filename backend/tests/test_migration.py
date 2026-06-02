"""Migration round-trip: apply head, insert one row per table, query back; then downgrade."""

from __future__ import annotations

from alembic import command
from alembic.config import Config
from app.core.db import make_engine
from app.models import (
    AgentRun,
    AgentStep,
    AnalysisRun,
    ApiKey,
    AuditLog,
    Experiment,
    ExperimentMetric,
    Layer,
    Membership,
    Metric,
    MetricResult,
    Organization,
    Readout,
    SrmCheck,
    User,
    Variant,
    Workspace,
)
from app.models.enums import (
    AgentStepKind,
    AgentType,
    AuditActorKind,
    ExperimentMetricRole,
    MetricType,
)
from sqlalchemy import inspect
from sqlmodel import Session, select


def test_full_graph_roundtrip(session: Session) -> None:
    """Insert a connected row in every table, then read several back."""
    org = Organization(name="Acme", slug="acme")
    session.add(org)
    session.commit()
    session.refresh(org)
    oid = org.id

    user = User(email="ds@acme.test", name="Priya")
    layer = Layer(org_id=oid, workspace_id=oid, name="checkout-layer")  # ws id set below
    session.add(user)
    session.commit()
    session.refresh(user)

    ws = Workspace(org_id=oid, name="Web", slug="web")
    session.add(ws)
    session.commit()
    session.refresh(ws)

    layer.workspace_id = ws.id
    session.add(layer)
    session.add(Membership(org_id=oid, user_id=user.id))
    session.add(ApiKey(org_id=oid, name="server", hashed_key="deadbeef", scopes=["assign"]))
    session.add(
        AuditLog(
            org_id=oid, actor_kind=AuditActorKind.system, action="create", target_type="experiment"
        )
    )
    session.commit()
    session.refresh(layer)

    metric = Metric(
        org_id=oid, workspace_id=ws.id, key="conv", name="Conversion", type=MetricType.proportion
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)

    exp = Experiment(
        org_id=oid,
        workspace_id=ws.id,
        key="checkout",
        name="Checkout",
        layer_id=layer.id,
        owner_id=user.id,
        salt="checkout",
    )
    session.add(exp)
    session.commit()
    session.refresh(exp)

    control = Variant(
        org_id=oid, experiment_id=exp.id, key="control", is_control=True, allocation_pct=50
    )
    treat = Variant(org_id=oid, experiment_id=exp.id, key="treatment", allocation_pct=50)
    session.add(control)
    session.add(treat)
    session.add(
        ExperimentMetric(
            org_id=oid,
            experiment_id=exp.id,
            metric_id=metric.id,
            role=ExperimentMetricRole.primary,
            is_oec=True,
        )
    )
    session.commit()
    session.refresh(control)

    run = AnalysisRun(org_id=oid, experiment_id=exp.id)
    session.add(run)
    session.commit()
    session.refresh(run)

    session.add(
        MetricResult(
            org_id=oid,
            analysis_run_id=run.id,
            metric_id=metric.id,
            variant_id=control.id,
            n=1000,
            estimate=0.12,
        )
    )
    session.add(
        SrmCheck(
            org_id=oid,
            analysis_run_id=run.id,
            chi_square=0.4,
            p_value=0.5,
            observed={"control": 500},
            expected={"control": 500},
        )
    )
    session.add(
        Readout(org_id=oid, experiment_id=exp.id, analysis_run_id=run.id, body_markdown="TL;DR")
    )
    session.commit()

    agent_run = AgentRun(
        org_id=oid, experiment_id=exp.id, agent_type=AgentType.analyst, model="claude-sonnet-4-6"
    )
    session.add(agent_run)
    session.commit()
    session.refresh(agent_run)
    session.add(
        AgentStep(
            org_id=oid,
            agent_run_id=agent_run.id,
            seq=0,
            kind=AgentStepKind.tool_call,
            tool_name="run_analysis",
        )
    )
    session.commit()

    # read back
    got = session.exec(select(Experiment).where(Experiment.key == "checkout")).one()
    assert got.salt == "checkout"
    assert got.owner_id == user.id
    variants = session.exec(select(Variant).where(Variant.experiment_id == got.id)).all()
    assert {v.key for v in variants} == {"control", "treatment"}
    assert sum(v.allocation_pct for v in variants) == 100
    assert session.exec(select(MetricResult)).one().n == 1000


def test_migration_downgrade(db_url: str) -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    tables = inspect(make_engine(db_url)).get_table_names()
    assert "organization" not in tables
    assert "experiment" not in tables
