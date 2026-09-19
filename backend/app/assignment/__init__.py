"""Pure, deterministic assignment / bucketing (P04).

No I/O, no globals (see docs/04-statistics-engine.md#assignment). The API builds
``ExperimentSpec`` objects from DB rows and calls :func:`assign`.
"""

from app.assignment.bucketing import bucket
from app.assignment.engine import assign
from app.assignment.spec import Assignment, ExperimentSpec, LayerSlot, VariantSpec
from app.assignment.targeting import evaluate_targeting

__all__ = [
    "Assignment",
    "ExperimentSpec",
    "LayerSlot",
    "VariantSpec",
    "assign",
    "bucket",
    "evaluate_targeting",
]
