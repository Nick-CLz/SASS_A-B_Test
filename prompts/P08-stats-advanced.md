# P08 — Statistics engine: advanced (M4) — correctness-critical

**Goal:** the rigor that sets Mallard apart: CUPED variance reduction, sequential/always-valid
inference, Bayesian analysis, and segment breakdowns. Builds on P07.

**Read first:** `docs/04-statistics-engine.md` §CUPED, §Sequential testing, §Bayesian,
§Heterogeneous treatment effects; `docs/05-ai-agents.md` (these become Analyst tools).

## Deliverables (pure, in `app/stats/`)
- `variance_reduction.py` — **CUPED**: `θ = Cov(Y,X)/Var(X)`, adjusted outcome, adjusted
  variance; returns θ and the variance-reduction ratio. (Sufficient stats from the P06 adapter.)
- `sequential.py` — at least one **always-valid** method (mSPRT *or* a confidence sequence) so
  peeking is safe; document the method and its assumptions. Optionally a group-sequential
  (alpha-spending) variant. Returns time-uniform intervals + an always-valid p-value/decision.
- `bayesian.py` — Beta–Binomial (conversion) and Normal (continuous) posteriors;
  **P(treatment > control)**, **credible interval**, **expected loss**; multi-arm "prob best".
- `segments.py` — pre-registered segment breakdowns with multiple-comparison control; a
  Simpson's-paradox warning when aggregate vs. segment effects disagree.

## Acceptance criteria
- **CUPED:** on synthetic data with a covariate correlated ρ with the outcome, variance drops by
  ≈ ρ² and the estimate stays unbiased (simulation test); CIs are tighter than P07's.
- **Sequential:** under repeated peeking on A/A data, the false-positive rate stays ≤ α
  (simulation) — the whole point. A true effect is detected with the documented properties.
- **Bayesian:** posteriors match conjugate closed-form on fixtures; `P(better)` and expected
  loss are calibrated on simulated data; agrees directionally with frequentist on clear cases.
- **Segments:** correction applied; Simpson's-paradox warning fires on a constructed example.
- Pure, seeded, `mypy`/`ruff` clean; cross-checked against references where possible.

## Notes
- Make the sequential method the default for the "live monitoring" path later; the fixed-horizon
  test (P07) is shown only at the pre-registered sample size (see `docs/04` UX rule).
- All four modules must be callable as **tools** by the Analyst agent (P14) — keep signatures
  clean and outputs JSON-serializable.

## If you must split this
CUPED → sequential → Bayesian → segments, each with its calibration test green before the next.

## Commit
`feat: cuped`, `feat: sequential inference`, `feat: bayesian`, `feat: segment analysis`.
Suggested model: **large**.
