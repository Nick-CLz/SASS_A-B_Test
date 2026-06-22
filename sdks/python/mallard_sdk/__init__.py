"""Mallard Python SDK — deterministic assignment + privacy-guarded event tracking."""

from mallard_sdk.bucketing import bucket
from mallard_sdk.client import Mallard
from mallard_sdk.engine import assign, evaluate_targeting
from mallard_sdk.privacy import PIIError, assert_no_pii, assert_pseudonymous_unit
from mallard_sdk.spec import Assignment, ExperimentSpec, LayerSlot, VariantSpec

__all__ = [
    "Assignment",
    "ExperimentSpec",
    "LayerSlot",
    "Mallard",
    "PIIError",
    "VariantSpec",
    "assert_no_pii",
    "assert_pseudonymous_unit",
    "assign",
    "bucket",
    "evaluate_targeting",
]
