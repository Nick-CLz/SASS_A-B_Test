"""Experiment service invariants (one control; allocations sum to 100) + creation helper."""

from __future__ import annotations

import pytest
from app.models import Experiment, Organization, Variant, Workspace
from app.services import experiments as svc
from app.services.experiments import ExperimentInvariantError
from sqlmodel import Session, select


def _org_and_workspace(session: Session) -> tuple[Organization, Workspace]:
    org = Organization(name="Acme", slug="acme")
    session.add(org)
    session.commit()
    session.refresh(org)
    ws = Workspace(org_id=org.id, name="Web", slug="web")
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return org, ws


def test_rejects_two_controls(session: Session) -> None:
    org, ws = _org_and_workspace(session)
    exp = Experiment(org_id=org.id, workspace_id=ws.id, key="x", name="X")
    variants = [
        Variant(key="control", is_control=True, allocation_pct=50),
        Variant(key="t", is_control=True, allocation_pct=50),
    ]
    with pytest.raises(ExperimentInvariantError, match="control"):
        svc.create_experiment_with_variants(session, exp, variants)


def test_rejects_allocations_not_summing_to_100(session: Session) -> None:
    org, ws = _org_and_workspace(session)
    exp = Experiment(org_id=org.id, workspace_id=ws.id, key="x", name="X")
    variants = [
        Variant(key="control", is_control=True, allocation_pct=40),
        Variant(key="t", is_control=False, allocation_pct=40),
    ]
    with pytest.raises(ExperimentInvariantError, match="sum to 100"):
        svc.create_experiment_with_variants(session, exp, variants)


def test_create_experiment_happy_path(session: Session) -> None:
    org, ws = _org_and_workspace(session)
    exp = Experiment(org_id=org.id, workspace_id=ws.id, key="checkout", name="Checkout")
    variants = [
        Variant(key="control", is_control=True, allocation_pct=50),
        Variant(key="treatment", is_control=False, allocation_pct=50),
    ]
    saved = svc.create_experiment_with_variants(session, exp, variants)

    assert saved.salt == "checkout"  # defaulted from key
    rows = session.exec(select(Variant).where(Variant.experiment_id == saved.id)).all()
    assert len(rows) == 2
    assert all(v.org_id == org.id for v in rows)
    assert all(v.experiment_id == saved.id for v in rows)
