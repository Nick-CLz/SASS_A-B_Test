"""Pure statistics engine — frequentist core (P07) + advanced methods (P08).

No I/O, no globals. Input = sufficient statistics (or per-unit arrays for CUPED); output =
typed result objects. Agents call this as tools and never compute statistics themselves
(see docs/04-statistics-engine.md, docs/05-ai-agents.md).
"""

from app.stats.bayesian import BayesianResult, beta_binomial_compare
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
from app.stats.variance_reduction import cuped, cuped_theta

__all__ = [
    "BayesianResult",
    "EffectResult",
    "MeanArm",
    "ProportionArm",
    "SrmResult",
    "benjamini_hochberg",
    "beta_binomial_compare",
    "bonferroni",
    "cuped",
    "cuped_theta",
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
