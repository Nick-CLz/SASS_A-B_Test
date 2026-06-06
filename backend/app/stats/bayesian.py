"""Bayesian analysis for conversion metrics (Beta-Binomial conjugate).

Reports P(treatment > control), a credible interval for the difference, and expected loss
(the expected regret of shipping the wrong arm) — a clean decision rule. See
docs/04-statistics-engine.md §Bayesian. Pure (Monte-Carlo from the posterior; seeded).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BayesianResult:
    control_rate: float
    treatment_rate: float
    prob_treatment_better: float
    ci_lower: float  # 95% credible interval for (treatment - control)
    ci_upper: float
    expected_loss_ship_treatment: float
    expected_loss_ship_control: float


def beta_binomial_compare(
    control_n: int,
    control_successes: int,
    treatment_n: int,
    treatment_successes: int,
    *,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    samples: int = 200_000,
    seed: int = 0,
) -> BayesianResult:
    """Posterior comparison of two conversion rates under Beta(prior) priors."""
    rng = np.random.default_rng(seed)
    control = rng.beta(
        prior_alpha + control_successes, prior_beta + control_n - control_successes, samples
    )
    treatment = rng.beta(
        prior_alpha + treatment_successes, prior_beta + treatment_n - treatment_successes, samples
    )
    diff = treatment - control
    lower, upper = np.quantile(diff, [0.025, 0.975])
    return BayesianResult(
        control_rate=control_successes / control_n if control_n else 0.0,
        treatment_rate=treatment_successes / treatment_n if treatment_n else 0.0,
        prob_treatment_better=float((treatment > control).mean()),
        ci_lower=float(lower),
        ci_upper=float(upper),
        # E[regret] = expected amount by which the *other* arm beats the chosen one.
        expected_loss_ship_treatment=float(np.maximum(control - treatment, 0).mean()),
        expected_loss_ship_control=float(np.maximum(treatment - control, 0).mean()),
    )
