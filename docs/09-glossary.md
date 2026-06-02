# 09 — Glossary

Plain-language definitions so the build model (and any reader) shares our vocabulary. Where a
term drives code, the relevant doc is linked.

- **A/B test / experiment** — a randomized comparison of a control and one or more treatments.
- **A/A test** — control vs. control; used to validate the pipeline (should show no effect; used
  for calibration). See [`04`](./04-statistics-engine.md).
- **Randomization unit** — the entity randomized (user, session, device, account). Same unit →
  same variant, always.
- **Analysis unit** — the unit a metric is measured on. If it differs from the randomization
  unit (e.g. randomize by user, measure per session), use the **delta method**.
- **Variant / arm** — a version in the experiment; one is the **control**.
- **Assignment / bucketing** — deterministically mapping a unit to a variant via a hash. See
  [`04 §Assignment`](./04-statistics-engine.md#assignment).
- **Salt / seed** — per-experiment string mixed into the hash so experiments are independent
  (orthogonal); changing it reshuffles assignment.
- **Layer** — a mutual-exclusion group: experiments in one layer never co-assign a unit;
  different layers overlap independently.
- **Holdout / holdback** — a reserved slice that never gets treatment, to measure cumulative
  shipped impact.
- **Exposure / trigger** — the moment a unit actually experiences its variant; analysis counts
  only exposed units to avoid **dilution**.
- **Dilution** — including unexposed units, which shrinks the measured effect toward zero.
- **OEC (Overall Evaluation Criterion)** — the single primary metric a decision is made on.
- **Guardrail metric** — a metric that must not regress (latency, crashes, revenue) even if the
  OEC improves.
- **Metric types** — **proportion** (binary/conversion), **mean** (continuous), **count**,
  **ratio** (needs the delta method).
- **Effect / lift** — absolute effect = treatment − control; **relative lift** = effect /
  control (a ratio → delta-method CI).
- **Confidence interval (CI)** — a range for the true effect; significance = excludes 0 after
  correction.
- **p-value** — probability of data this extreme if there were no effect; small → evidence of an
  effect. Peeking at fixed-horizon p-values inflates false positives — hence **sequential**.
- **Welch's t-test** — t-test allowing unequal variances; the safe default for means.
- **Two-proportion z-test** — significance test for conversion-rate differences.
- **Delta method** — first-order approximation for the variance of a ratio of random
  quantities; used for ratio metrics and relative-lift CIs.
- **CUPED** — variance reduction using a pre-experiment covariate; tighter CIs, same users. See
  [`04 §CUPED`](./04-statistics-engine.md).
- **CUPAC** — CUPED where the covariate is an ML model's prediction (stretch).
- **Sequential testing / always-valid inference** — methods (mSPRT, GAVI, group-sequential)
  whose intervals are valid at every peek, so monitoring never inflates error.
- **Bayesian analysis** — posterior **P(treatment > control)**, **credible interval**, and
  **expected loss** (risk of shipping the wrong arm).
- **SRM (Sample Ratio Mismatch)** — observed arm split ≠ intended split (chi-square test). A red
  flag that the experiment is broken; results must not be trusted.
- **Multiple comparisons** — testing many metrics/variants inflates false positives; corrected
  with **Bonferroni/Holm** (family-wise) or **Benjamini–Hochberg** (FDR).
- **Power / MDE** — power = chance of detecting a true effect; **MDE** = smallest effect
  detectable at a given n, α, power. Drives sample size & runtime.
- **Novelty / primacy effect** — treatment effect that changes over time as users get used to a
  change.
- **Heterogeneous treatment effect (HTE) / CATE** — effects that differ by segment.
- **Simpson's paradox** — aggregate and segment effects point opposite ways; a segmentation
  warning.
- **Sufficient statistics** — the summaries (counts, sums, sums-of-squares, covariances) the
  stats engine needs; the only thing crossing from analytics → stats. Keeps the engine pure and
  warehouse-portable.
- **Warehouse-native** — running the analytics in the customer's own data warehouse so raw data
  never leaves their perimeter. See [`02`](./02-architecture.md).
- **Grounding (AI)** — agents only report numbers obtained from tool calls into the engine;
  never LLM-computed. See [`05`](./05-ai-agents.md).
- **Agent run / step** — the recorded trace of an AI agent's tool calls and outputs; the audit
  trail behind grounding.
- **PII guard** — ingestion check that rejects/redacts personal data so none reaches storage.
