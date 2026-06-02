# 04 — Statistics engine

This is the technical heart and the credibility core. The engine is **pure** (no I/O), takes
**sufficient statistics**, and returns estimates, intervals, p-values, and diagnostics. Every
method here must ship with unit tests against textbook fixtures and, where possible, a
simulation that confirms calibration (e.g. an A/A test yields a uniform p-value distribution
and ~α false-positive rate).

> Implementation note for the build: keep functions stateless and typed, group by topic
> (`stats/frequentist.py`, `stats/bayesian.py`, `stats/sequential.py`, `stats/variance_reduction.py`,
> `stats/diagnostics.py`, `stats/power.py`). NumPy/SciPy/statsmodels do the heavy lifting; we
> own the orchestration, the ratio-metric handling, and the calibration tests.

---

## Assignment (randomization) {#assignment}
Not inference, but it must be right or everything downstream is wrong.

**Deterministic bucketing.** For unit `u` in experiment `e`:
```
h = hash( e.salt + ":" + u )         # stable 64-bit hash, e.g. SHA-256 → take 64 bits
x = h / 2^64  ∈ [0, 1)               # uniform in [0,1)
```
- **Eligibility/targeting** is evaluated first; ineligible units are not assigned and not
  counted.
- **Traffic allocation:** if the experiment takes `a%` of traffic, only `x < a/100` enters;
  the rest is "not in experiment."
- **Variant split:** partition `[0, a/100)` by each variant's `allocation_pct`.
- **Independence (orthogonality):** a different `salt` per experiment makes assignments across
  experiments independent in expectation. Concurrent experiments don't bias each other.
- **Mutual exclusion (layers):** experiments in one layer share a single partitioned hash
  space, so a unit lands in at most one of them. Different layers overlap independently.
- **Holdouts:** a reserved layer partition that never receives any treatment — used to measure
  the *cumulative* impact of all shipped changes.

**Tests:** uniformity of `x` (KS test), stability (same input → same variant), correct split
proportions at scale, orthogonality between two salts (assignment independence), exclusivity
within a layer.

---

## Core inference

### Metric types
- **Proportion** (binary): conversion rate. Two-proportion **z-test**; Wilson interval for the
  rate; CI for the difference.
- **Mean** (continuous): revenue, time-on-page. **Welch's t-test** (unequal variances — the
  safe default), CI for the difference of means.
- **Count** (per unit): treat as mean of per-unit counts (CLT applies at scale); optionally
  Poisson/NB for low counts.
- **Ratio** (analysis unit ≠ randomization unit, e.g. clicks-per-session while randomizing by
  user): the denominator is random, so a naive test understates variance. Use the **delta
  method** for the variance of the ratio.

### Effect & lift
- **Absolute effect:** `est_treatment − est_control`.
- **Relative lift:** `(est_treatment − est_control) / est_control`, with a CI via the **delta
  method** (lift is a ratio of random quantities). PMs think in relative lift, so this matters.

### Confidence intervals
Report a CI for every effect, not just a p-value. Significance = CI excludes 0 (after
correction). The UI leads with the interval; the agent narrates it.

---

## Delta method (ratio metrics & relative lift)
For a ratio `R = X̄/Ȳ` of two per-unit averages, the variance is approximated by:
```
Var(R) ≈ (1/Ȳ²)·Var(X̄) + (X̄²/Ȳ⁴)·Var(Ȳ) − 2·(X̄/Ȳ³)·Cov(X̄, Ȳ)
```
Used both for **ratio metrics** and for the **relative lift** CI. This is the single most
common thing naive tools get wrong (they treat sessions as independent when users are the
randomization unit), which silently inflates false positives. Getting it right is a credibility
signal.

---

## Variance reduction

### CUPED (Controlled experiment Using Pre-Existing Data)
Use a pre-period covariate `X` (e.g. the same metric measured before the experiment) to remove
its explainable variance from the outcome `Y`:
```
Y_cuped = Y − θ·(X − E[X]),      θ = Cov(Y, X) / Var(X)
```
- Unbiased (because `E[X]` is the same across arms in expectation), and reduces variance by
  `ρ²` (the squared correlation of `Y` and `X`) — often 30–50% tighter CIs, i.e. the same power
  with far fewer users or far less time.
- Needs the analytics layer to compute `Cov(Y, X)` and `Var(X)` (sufficient stats) — cheap.
- **CUPAC** (stretch): replace the single covariate with an ML model's prediction as the
  control variate.

This is a marquee feature — it's exactly the kind of rigor a senior DS interviewer probes for.

---

## Sequential testing (peek any time, safely)
The biggest real-world failure mode: people watch the dashboard and stop the moment it's
"significant," which wildly inflates the false-positive rate under fixed-horizon tests. Mallard
makes **continuous monitoring safe by default**.

Provide at least one always-valid approach (implement one well, document the others):
- **Always-valid inference / confidence sequences (mSPRT or GAVI):** intervals valid at *every*
  time, so peeking never inflates Type I error. Default for the monitoring view. (Refs:
  Johari–Pekelis–Walsh "Always Valid Inference"; Howard et al. time-uniform bounds.)
- **Group-sequential (O'Brien–Fleming / Pocock, alpha-spending):** if a fixed number of planned
  interim looks is preferred.

**UX rule:** the live dashboard shows the *sequential* interval; the *fixed-horizon* test is
only shown when the experiment reaches its pre-registered sample size. The Analyst agent always
states which regime a number came from.

---

## Bayesian analysis
Complementary, often more intuitive for PMs.
- **Conversion:** Beta–Binomial conjugate posterior per arm.
- **Continuous:** Normal posterior (Normal–Normal / via CLT).
- Report **P(treatment > control)**, a **credible interval**, and **expected loss / risk**
  (expected regret of shipping the wrong arm) — the latter is a clean decision rule:
  ship when expected loss < a small threshold.
- Multi-arm: **probability each arm is best**; optional Thompson-sampling allocation (stretch).

---

## Diagnostics & data quality (the part that prevents wrong conclusions)

### Sample Ratio Mismatch (SRM)
A **chi-square goodness-of-fit** test comparing observed arm counts to the intended split. A
significant SRM (commonly p < 0.001) means the randomization or logging is broken and **the
results must not be trusted** — surfaced loudly in the UI and always checked first by the
Analyst agent.

### A/A testing
Built-in A/A mode to validate the whole pipeline: over many simulated A/A experiments the
p-value distribution must be ~uniform and the false-positive rate ~α. Ships as a calibration
test in CI.

### Multiple comparisons
When testing many metrics or many variants, control error:
- **Bonferroni / Holm** for strict family-wise error (few guardrails).
- **Benjamini–Hochberg FDR** when scanning many secondary metrics/segments.
The chosen correction is recorded in `method_detail` and stated in the readout.

### Other checks
- **Novelty / primacy effects:** plot treatment effect by days-since-exposure; flag drift.
- **Triggered / exposed analysis:** count only exposed units to avoid dilution.
- **Outliers:** optional winsorization for heavy-tailed revenue metrics (recorded as method).
- **Segment sanity / Simpson's paradox:** warn when aggregate and segment effects disagree.

---

## Power & sample size
- **Sample size** for a target MDE, α, and power (proportions and means).
- **MDE** achievable for a given n / runtime.
- **Runtime estimate** from observed traffic.
- **Effect of CUPED:** show how variance reduction shrinks the required n / runtime — a great
  demo moment.
The Designer agent calls these to propose a defensible duration before launch; underpowered
designs are flagged.

---

## Heterogeneous treatment effects (segments) — partly stretch
- Pre-registered **segment breakdowns** (country, platform, new vs. returning) with
  multiple-comparison control.
- Honest warnings about post-hoc segment fishing.
- Stretch: uplift modeling / CATE estimators for "who responds best."

---

## What the engine returns (contract)
For each metric × variant the engine returns a typed result object carrying: `n`, `estimate`,
`abs_effect`, `rel_effect`, `ci_lower/upper` (and the regime: fixed vs. sequential), `p_value`
and/or `prob_to_beat_control` + `expected_loss`, `variance`, `std_error`, `is_significant`, and
a `method_detail` blob (exact test, df, correction, CUPED θ, winsorization, etc.). This maps
1:1 to `metric_result` in [`03-data-model.md`](./03-data-model.md). **Every field is computed,
never LLM-generated.**

## Testing standard (non-negotiable)
1. **Textbook fixtures:** each test reproduces a known worked example to N decimals.
2. **Calibration via simulation:** A/A → uniform p-values, ~α FPR; powered A/B → ~target power.
3. **Property tests:** symmetry, monotonicity (more data → tighter CI), invariance to unit
   ordering.
4. **Cross-checks:** validate against `statsmodels`/`scipy` where an equivalent exists.

If a method can't pass calibration, it doesn't ship — this is the line that separates Mallard
from "naive z-test" tools.
