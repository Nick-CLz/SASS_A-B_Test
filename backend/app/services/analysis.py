"""Analysis pipeline: sufficient stats -> SRM first -> per-metric tests -> correction ->
persist. The seam the dashboard and the Analyst agent both consume (docs/02 §Analyze flow).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, desc, select

from app.analytics.store import DuckStore
from app.core.errors import InvariantError, NotFoundError
from app.models.analysis import AnalysisRun, MetricResult, SrmCheck
from app.models.enums import AnalysisStatus, AnalysisTrigger, MetricType
from app.models.experiment import Metric, Variant
from app.services import experiments as exp_svc
from app.services.repository import add
from app.stats import (
    MeanArm,
    ProportionArm,
    benjamini_hochberg,
    beta_binomial_compare,
    bonferroni,
    holm,
    srm_check,
    two_proportion_z_test,
    welch_t_test,
)
from app.stats.results import EffectResult

_CORRECTIONS = {
    "bonferroni": bonferroni,
    "holm": holm,
    "benjamini_hochberg": benjamini_hochberg,
}


@dataclass
class _Row:
    metric: Metric
    variant: Variant
    n: int
    estimate: float | None
    effect: EffectResult | None  # None for the control arm
    adjusted: tuple[bool, float] | None = None
    prob_better: float | None = None  # Bayesian P(treatment > control)
    expected_loss: float | None = None  # Bayesian expected regret of shipping treatment


def _event_name(metric: Metric) -> str:
    return str((metric.numerator or {}).get("event", metric.key))


def analyze_experiment(
    session: Session,
    store: DuckStore,
    org_id: uuid.UUID,
    workspace_id: uuid.UUID,
    key: str,
    alpha: float = 0.05,
    correction: str = "benjamini_hochberg",
    bayesian: bool = True,
) -> uuid.UUID:
    """Run one analysis and persist an AnalysisRun + MetricResults + SrmCheck."""
    exp = exp_svc.get_experiment(session, workspace_id, key)
    variants = exp_svc.get_variants(session, exp.id)
    control = next((v for v in variants if v.is_control), None)
    if control is None:
        raise InvariantError("experiment has no control variant")
    ws = str(workspace_id)

    run = AnalysisRun(
        org_id=org_id,
        experiment_id=exp.id,
        status=AnalysisStatus.complete,
        trigger=AnalysisTrigger.manual,
        method={"alpha": alpha, "correction": correction, "bayesian": bayesian},
    )
    add(session, run)

    # SRM first — a mismatch invalidates the results.
    counts = store.exposure_counts(ws, key)
    if counts:
        allocation = {v.key: v.allocation_pct for v in variants}
        observed = {k: int(counts.get(k, 0)) for k in allocation}
        srm = srm_check(observed, allocation)
        session.add(
            SrmCheck(
                org_id=org_id,
                analysis_run_id=run.id,
                chi_square=srm.chi_square,
                p_value=srm.p_value,
                observed=observed,
                expected=srm.expected,
                is_mismatch=srm.is_mismatch,
            )
        )

    rows = _compute_rows(store, ws, key, variants, control, session, exp.id, alpha, bayesian)
    _apply_correction(rows, correction, alpha)
    _persist(session, run.id, org_id, rows)
    session.commit()
    return run.id


def _compute_rows(
    store: DuckStore,
    ws: str,
    key: str,
    variants: list[Variant],
    control: Variant,
    session: Session,
    experiment_id: uuid.UUID,
    alpha: float,
    bayesian: bool = True,
) -> list[_Row]:
    rows: list[_Row] = []
    for link in exp_svc.get_experiment_metrics(session, experiment_id):
        metric = session.get(Metric, link.metric_id)
        if metric is None:
            continue
        event = _event_name(metric)
        if metric.type == MetricType.proportion:
            p_arms = store.proportion_stats(ws, key, event)
            p_control = ProportionArm(*p_arms.get(control.key, (0, 0)))
            for variant in variants:
                n, s = p_arms.get(variant.key, (0, 0))
                if variant.is_control:
                    rows.append(_Row(metric, variant, n, p_control.rate, None))
                else:
                    eff = two_proportion_z_test(p_control, ProportionArm(n, s), alpha)
                    prob_better: float | None = None
                    expected_loss: float | None = None
                    if bayesian:
                        bayes = beta_binomial_compare(
                            p_control.n, p_control.successes, n, s, samples=50_000
                        )
                        prob_better = bayes.prob_treatment_better
                        expected_loss = bayes.expected_loss_ship_treatment
                    rows.append(
                        _Row(
                            metric,
                            variant,
                            n,
                            eff.estimate,
                            eff,
                            prob_better=prob_better,
                            expected_loss=expected_loss,
                        )
                    )
        else:
            use_value = metric.type == MetricType.mean
            c_arms = store.continuous_stats(ws, key, event, use_value=use_value)
            c_control = MeanArm(*c_arms.get(control.key, (0, 0.0, 0.0)))
            for variant in variants:
                stat = c_arms.get(variant.key, (0, 0.0, 0.0))
                if variant.is_control:
                    rows.append(_Row(metric, variant, stat[0], c_control.mean, None))
                else:
                    eff = welch_t_test(c_control, MeanArm(*stat), alpha)
                    rows.append(_Row(metric, variant, stat[0], eff.estimate, eff))
    return rows


def _apply_correction(rows: list[_Row], correction: str, alpha: float) -> None:
    treatment_rows = [r for r in rows if r.effect is not None]
    if not treatment_rows or correction not in _CORRECTIONS:
        return
    pvalues = [r.effect.p_value for r in treatment_rows if r.effect is not None]
    for row, (reject, adjusted) in zip(
        treatment_rows, _CORRECTIONS[correction](pvalues, alpha), strict=True
    ):
        row.adjusted = (reject, adjusted)


def _persist(session: Session, run_id: uuid.UUID, org_id: uuid.UUID, rows: list[_Row]) -> None:
    for row in rows:
        eff = row.effect
        is_significant = eff.is_significant if eff is not None else False
        detail: dict[str, Any] = dict(eff.method_detail) if eff is not None else {"role": "control"}
        if eff is not None and row.adjusted is not None:
            is_significant, adjusted_p = row.adjusted
            detail["adjusted_p"] = adjusted_p
        session.add(
            MetricResult(
                org_id=org_id,
                analysis_run_id=run_id,
                metric_id=row.metric.id,
                variant_id=row.variant.id,
                n=row.n,
                estimate=row.estimate,
                abs_effect=eff.abs_effect if eff is not None else None,
                rel_effect=eff.rel_effect if eff is not None else None,
                ci_lower=eff.ci_lower if eff is not None else None,
                ci_upper=eff.ci_upper if eff is not None else None,
                p_value=eff.p_value if eff is not None else None,
                std_error=eff.std_error if eff is not None else None,
                prob_to_beat_control=row.prob_better,
                expected_loss=row.expected_loss,
                is_significant=is_significant,
                method_detail=detail,
            )
        )


def latest_run(session: Session, experiment_id: uuid.UUID) -> AnalysisRun:
    run = session.exec(
        select(AnalysisRun)
        .where(AnalysisRun.experiment_id == experiment_id)
        .order_by(desc(AnalysisRun.computed_at))
    ).first()
    if run is None:
        raise NotFoundError("no analysis has been run for this experiment yet")
    return run


def run_rows(session: Session, run_id: uuid.UUID) -> list[MetricResult]:
    return list(
        session.exec(select(MetricResult).where(MetricResult.analysis_run_id == run_id)).all()
    )


def run_srm(session: Session, run_id: uuid.UUID) -> SrmCheck | None:
    return session.exec(select(SrmCheck).where(SrmCheck.analysis_run_id == run_id)).first()
