"""Experiment service logic: invariants + a creation helper.

The full lifecycle state machine and REST surface arrive in P03; P02 provides the seam
plus the core variant invariants (exactly one control; allocations sum to 100).
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlmodel import Session

from app.models.experiment import Experiment, Variant
from app.services.repository import add

ALLOCATION_TOLERANCE = 0.01


class ExperimentInvariantError(ValueError):
    """Raised when experiment/variant invariants are violated."""


def ensure_single_control(variants: Sequence[Variant]) -> None:
    """Exactly one variant must be the control."""
    controls = [v for v in variants if v.is_control]
    if len(controls) != 1:
        raise ExperimentInvariantError(
            f"exactly one control variant required, found {len(controls)}"
        )


def validate_variant_allocations(variants: Sequence[Variant]) -> None:
    """Variant allocations must sum to 100%."""
    if not variants:
        raise ExperimentInvariantError("at least one variant is required")
    total = sum(v.allocation_pct for v in variants)
    if abs(total - 100.0) > ALLOCATION_TOLERANCE:
        raise ExperimentInvariantError(f"variant allocations must sum to 100, got {total}")


def validate_variants(variants: Sequence[Variant]) -> None:
    """Run all variant-level invariants."""
    validate_variant_allocations(variants)
    ensure_single_control(variants)


def create_experiment_with_variants(
    session: Session, experiment: Experiment, variants: list[Variant]
) -> Experiment:
    """Persist an experiment and its variants after checking invariants.

    The per-experiment ``salt`` defaults to the experiment ``key`` so bucketing is
    independent across experiments (see docs/04-statistics-engine.md#assignment).
    """
    validate_variants(variants)
    if not experiment.salt:
        experiment.salt = experiment.key
    add(session, experiment)
    for variant in variants:
        variant.experiment_id = experiment.id
        variant.org_id = experiment.org_id
        session.add(variant)
    session.commit()
    session.refresh(experiment)
    return experiment
