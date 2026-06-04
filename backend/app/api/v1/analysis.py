"""Analysis + results + power endpoints (see docs/06-api-and-sdk.md §Results)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.api.deps import SessionDep, StoreDep, TenantDep
from app.models.analysis import AnalysisRun
from app.models.experiment import Metric
from app.schemas.analysis import (
    AnalysisRunRead,
    AnalyzeRequest,
    MetricResultRead,
    PowerResponse,
    SrmRead,
)
from app.services import analysis as svc
from app.services import experiments as exp_svc
from app.stats.power import runtime_days, sample_size_proportion

router = APIRouter(prefix="/experiments", tags=["results"])


def _build_run_read(
    session: SessionDep, experiment_id: uuid.UUID, run: AnalysisRun
) -> AnalysisRunRead:
    variants = {v.id: v for v in exp_svc.get_variants(session, experiment_id)}
    metric_cache: dict[object, Metric | None] = {}
    results = []
    for mr in svc.run_rows(session, run.id):
        metric = metric_cache.setdefault(mr.metric_id, session.get(Metric, mr.metric_id))
        variant = variants.get(mr.variant_id)
        results.append(
            MetricResultRead(
                metric_key=metric.key if metric else "?",
                variant_key=variant.key if variant else "?",
                is_control=bool(variant.is_control) if variant else False,
                n=mr.n,
                estimate=mr.estimate,
                abs_effect=mr.abs_effect,
                rel_effect=mr.rel_effect,
                ci_lower=mr.ci_lower,
                ci_upper=mr.ci_upper,
                p_value=mr.p_value,
                prob_to_beat_control=mr.prob_to_beat_control,
                expected_loss=mr.expected_loss,
                is_significant=mr.is_significant,
                method_detail=mr.method_detail,
            )
        )
    srm_row = svc.run_srm(session, run.id)
    srm = (
        SrmRead(
            chi_square=srm_row.chi_square,
            p_value=srm_row.p_value,
            is_mismatch=srm_row.is_mismatch,
            observed=srm_row.observed,
            expected=srm_row.expected,
        )
        if srm_row is not None
        else None
    )
    return AnalysisRunRead(
        id=run.id,
        computed_at=run.computed_at,
        status=str(run.status),
        method=run.method,
        srm=srm,
        results=results,
    )


@router.post("/{key}/analyze", response_model=AnalysisRunRead)
def analyze(
    key: str, payload: AnalyzeRequest, session: SessionDep, ctx: TenantDep, store: StoreDep
) -> AnalysisRunRead:
    run_id = svc.analyze_experiment(
        session,
        store,
        ctx.org_id,
        ctx.workspace_id,
        key,
        payload.alpha,
        payload.correction,
        payload.bayesian,
    )
    exp = exp_svc.get_experiment(session, ctx.workspace_id, key)
    run = session.get(AnalysisRun, run_id)
    assert run is not None
    return _build_run_read(session, exp.id, run)


@router.get("/{key}/results", response_model=AnalysisRunRead)
def results(key: str, session: SessionDep, ctx: TenantDep) -> AnalysisRunRead:
    exp = exp_svc.get_experiment(session, ctx.workspace_id, key)
    run = svc.latest_run(session, exp.id)
    return _build_run_read(session, exp.id, run)


@router.get("/{key}/power", response_model=PowerResponse)
def power_analysis(
    key: str,
    session: SessionDep,
    ctx: TenantDep,
    baseline: float = Query(0.1, gt=0, lt=1),
    mde: float = Query(0.02, gt=0),
    alpha: float = 0.05,
    power: float = 0.8,
    daily_traffic: float | None = None,
) -> PowerResponse:
    exp_svc.get_experiment(session, ctx.workspace_id, key)  # 404 if missing
    per_arm = sample_size_proportion(baseline, mde, alpha, power)
    total = 2 * per_arm
    return PowerResponse(
        baseline=baseline,
        mde=mde,
        alpha=alpha,
        power=power,
        sample_size_per_arm=per_arm,
        total_sample_size=total,
        runtime_days=runtime_days(total, daily_traffic) if daily_traffic else None,
    )
