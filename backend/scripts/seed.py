"""Seed a local org + workspace + metric so you can drive the /v1 API by hand.

    cd backend && DATABASE_URL=sqlite:///./mallard.db uv run python -m scripts.seed

Prints the X-Workspace-Id to use and an admin API key (shown once). Idempotent: re-running
reuses the existing demo org/workspace/metric. Point the API server at the *same* DATABASE_URL
so they share one database (use a file, not in-memory). See docs/USAGE.md.
"""

from __future__ import annotations

from app.core.db import make_engine
from app.models import Metric, Organization, Workspace
from app.models.enums import MetricType
from app.services import api_keys as keys_svc
from sqlmodel import Session, SQLModel, select


def _get_or_create_org(session: Session) -> Organization:
    org = session.exec(select(Organization).where(Organization.slug == "demo")).first()
    if org is None:
        org = Organization(name="Demo Co", slug="demo")
        session.add(org)
        session.commit()
        session.refresh(org)
    return org


def _get_or_create_workspace(session: Session, org: Organization) -> Workspace:
    ws = session.exec(
        select(Workspace).where(Workspace.org_id == org.id, Workspace.slug == "web")
    ).first()
    if ws is None:
        ws = Workspace(org_id=org.id, name="Web", slug="web")
        session.add(ws)
        session.commit()
        session.refresh(ws)
    return ws


def _get_or_create_metric(session: Session, org: Organization, ws: Workspace) -> Metric:
    metric = session.exec(
        select(Metric).where(Metric.workspace_id == ws.id, Metric.key == "conv")
    ).first()
    if metric is None:
        metric = Metric(
            org_id=org.id,
            workspace_id=ws.id,
            key="conv",
            name="Purchase conversion",
            type=MetricType.proportion,
            numerator={"event": "purchase"},
        )
        session.add(metric)
        session.commit()
        session.refresh(metric)
    return metric


def main() -> None:
    engine = make_engine()
    SQLModel.metadata.create_all(engine)  # harmless if Alembic already created the tables
    with Session(engine) as session:
        org = _get_or_create_org(session)
        ws = _get_or_create_workspace(session, org)
        metric = _get_or_create_metric(session, org, ws)
        _, secret = keys_svc.create_api_key(session, org.id, "seed-admin", ["admin"])
        ws_id = str(ws.id)
        metric_id = str(metric.id)

    print("\nSeed complete. Drive the /v1 API with these:\n")
    print(f"  export WS={ws_id}")
    print(f"  export KEY={secret}    # admin API key — shown once, save it")
    print(f"  # primary metric 'conv' id: {metric_id}\n")
    print("  curl -s localhost:8000/v1/experiments \\")
    print('    -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY"\n')


if __name__ == "__main__":
    main()
