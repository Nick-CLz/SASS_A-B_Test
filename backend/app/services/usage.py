"""Usage metering: per-org counts for billing — AI agent runs + tokens, and analyses.

Derived from the existing trace tables (no separate write path); the **organization** is the
billing boundary. Powers ``GET /v1/usage`` and backs the metered-AI pricing in
``docs/11-sales.md``. Billing-provider integration (e.g. Stripe) sits on top of this.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.agent import AgentRun
from app.models.analysis import AnalysisRun
from app.models.base import utcnow


@dataclass
class UsageSummary:
    org_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    agent_runs: int
    agent_cost_tokens: int
    analyses: int
    agent_runs_by_type: dict[str, int] = field(default_factory=dict)


def _month_start(moment: datetime) -> datetime:
    return moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def usage_summary(
    session: Session,
    org_id: uuid.UUID,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> UsageSummary:
    """Aggregate billable usage for ``org_id`` over [since, until] (default: this month)."""
    until = until or utcnow()
    since = since or _month_start(until)

    grouped = session.exec(
        select(
            AgentRun.agent_type,
            func.count(),
            func.coalesce(func.sum(AgentRun.cost_tokens), 0),
        )
        .where(
            AgentRun.org_id == org_id,
            AgentRun.created_at >= since,
            AgentRun.created_at <= until,
        )
        .group_by(AgentRun.agent_type)
    ).all()

    by_type: dict[str, int] = {}
    runs = 0
    tokens = 0
    for agent_type, count, token_sum in grouped:
        by_type[str(agent_type)] = int(count)
        runs += int(count)
        tokens += int(token_sum)

    analyses = session.exec(
        select(func.count())
        .select_from(AnalysisRun)
        .where(
            AnalysisRun.org_id == org_id,
            AnalysisRun.created_at >= since,
            AnalysisRun.created_at <= until,
        )
    ).one()

    return UsageSummary(
        org_id=org_id,
        period_start=since,
        period_end=until,
        agent_runs=runs,
        agent_cost_tokens=tokens,
        analyses=int(analyses),
        agent_runs_by_type=by_type,
    )
