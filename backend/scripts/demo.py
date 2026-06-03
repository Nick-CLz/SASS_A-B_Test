"""Standalone beta demo of the Mallard experimentation engine.

Runs the whole flow on in-memory stores (SQLite + DuckDB) so it needs no Postgres,
Docker, or network:

    cd backend && uv run python -m scripts.demo

It creates two experiments, seeds synthetic exposures + conversion events with a known
effect (and one with an injected SRM), runs the real analysis pipeline, and prints a
plain-language readout — every number computed by the deterministic stats engine.
"""

from __future__ import annotations

from app.analytics.store import DuckStore
from app.analytics.synthetic import SyntheticSpec, generate_conversions
from app.models import Metric, Organization, Workspace
from app.models.enums import ExperimentMetricRole, ExperimentStatus, MetricType
from app.models.experiment import ExperimentMetric
from app.schemas.experiment import ExperimentCreate, VariantCreate
from app.services import analysis as analysis_svc
from app.services import experiments as exp_svc
from app.services.repository import add
from app.stats.power import sample_size_proportion
from sqlmodel import Session, SQLModel, create_engine


def _rule(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def _two_variants() -> list[VariantCreate]:
    return [
        VariantCreate(key="control", is_control=True, allocation_pct=50),
        VariantCreate(key="treatment", is_control=False, allocation_pct=50),
    ]


def _print_results(session: Session, run_id, exp_key: str, workspace_id) -> None:
    exp = exp_svc.get_experiment(session, workspace_id, exp_key)
    _rule(f"Experiment: {exp.name}  [{exp_key}]")
    print(f"  hypothesis: {exp.hypothesis}")

    srm = analysis_svc.run_srm(session, run_id)
    if srm is not None:
        status = "SRM MISMATCH -> results NOT trustworthy" if srm.is_mismatch else "SRM ok"
        print(
            f"  data quality: {status}  "
            f"(chi2={srm.chi_square:.1f}, p={srm.p_value:.2e}, observed={srm.observed})"
        )

    variants = {v.id: v for v in exp_svc.get_variants(session, exp.id)}
    for mr in analysis_svc.run_rows(session, run_id):
        variant = variants[mr.variant_id]
        if variant.is_control:
            print(f"  control   ({variant.key}): rate={mr.estimate:.3%}  n={mr.n:,}")
        else:
            verdict = "SIGNIFICANT" if mr.is_significant else "not significant"
            print(f"  treatment ({variant.key}): rate={mr.estimate:.3%}  n={mr.n:,}")
            print(
                f"      abs effect={mr.abs_effect:+.3%}  rel lift={mr.rel_effect:+.1%}  "
                f"CI=[{mr.ci_lower:+.3%}, {mr.ci_upper:+.3%}]  p={mr.p_value:.2e}  -> {verdict}"
            )


def _seed_experiment(
    session: Session,
    store: DuckStore,
    org: Organization,
    workspace: Workspace,
    metric: Metric,
    *,
    key: str,
    name: str,
    hypothesis: str,
    seed: int,
    control_rate: float,
    treatment_rate: float,
    control_fraction: float = 0.5,
) -> str:
    exp = exp_svc.create_experiment(
        session,
        org.id,
        workspace.id,
        ExperimentCreate(key=key, name=name, hypothesis=hypothesis, variants=_two_variants()),
    )
    session.add(
        ExperimentMetric(
            org_id=org.id,
            experiment_id=exp.id,
            metric_id=metric.id,
            role=ExperimentMetricRole.primary,
            is_oec=True,
            min_detectable_effect=0.02,
        )
    )
    session.commit()
    exp_svc.transition_experiment(session, workspace.id, key, ExperimentStatus.review)
    exp_svc.transition_experiment(session, workspace.id, key, ExperimentStatus.running)
    generate_conversions(
        store,
        SyntheticSpec(
            workspace_id=str(workspace.id),
            experiment_key=key,
            n=20000,
            seed=seed,
            control_fraction=control_fraction,
        ),
        control_rate=control_rate,
        treatment_rate=treatment_rate,
    )
    return key


def main() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    store = DuckStore(":memory:")

    _rule("Mallard beta demo  (in-memory SQLite + DuckDB; no external services)")
    with Session(engine) as session:
        org = add(session, Organization(name="Demo Co", slug="demo"))
        workspace = add(session, Workspace(org_id=org.id, name="Web", slug="web"))
        metric = add(
            session,
            Metric(
                org_id=org.id,
                workspace_id=workspace.id,
                key="conv",
                name="Purchase conversion",
                type=MetricType.proportion,
                numerator={"event": "purchase"},
            ),
        )

        winner = _seed_experiment(
            session,
            store,
            org,
            workspace,
            metric,
            key="checkout_v2",
            name="New checkout",
            hypothesis="A cleaner checkout lifts purchase conversion.",
            seed=1,
            control_rate=0.10,
            treatment_rate=0.14,
        )
        broken = _seed_experiment(
            session,
            store,
            org,
            workspace,
            metric,
            key="banner_color",
            name="Banner color",
            hypothesis="A green banner increases purchases.",
            seed=2,
            control_rate=0.10,
            treatment_rate=0.10,
            control_fraction=0.62,
        )

        for key in (winner, broken):
            run_id = analysis_svc.analyze_experiment(session, store, org.id, workspace.id, key)
            _print_results(session, run_id, key, workspace.id)

    _rule("Power: detect a +2pp lift on a 10% baseline (alpha=0.05, power=0.80)")
    per_arm = sample_size_proportion(0.10, 0.02)
    print(f"  required sample size: {per_arm:,} per arm  ({2 * per_arm:,} total)")
    print("\nDone. This same pipeline runs behind the /v1 API and the AI agents (P11-P14).\n")


if __name__ == "__main__":
    main()
