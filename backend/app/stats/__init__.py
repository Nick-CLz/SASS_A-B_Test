"""Pure statistics engine — frequentist core (P07); advanced methods in P08.

No I/O, no globals. Input = sufficient statistics; output = typed result objects.
Agents call this as tools and never compute statistics themselves
(see docs/04-statistics-engine.md, docs/05-ai-agents.md).
"""

from app.stats.diagnostics import benjamini_hochberg, bonferroni, holm, srm_check
from app.stats.frequentist import (
    two_proportion_z_test,
    welch_t_test,
    wilson_interval,
    winsorize,
)
from app.stats.power import (
    mde_proportion,
    runtime_days,
    sample_size_mean,
    sample_size_proportion,
)
from app.stats.results import EffectResult, MeanArm, ProportionArm, SrmResult

__all__ = [
    "EffectResult",
    "MeanArm",
    "ProportionArm",
    "SrmResult",
    "benjamini_hochberg",
    "bonferroni",
    "holm",
    "mde_proportion",
    "runtime_days",
    "sample_size_mean",
    "sample_size_proportion",
    "srm_check",
    "two_proportion_z_test",
    "welch_t_test",
    "wilson_interval",
    "winsorize",
]
