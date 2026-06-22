# Case study — Mallard: an AI-native, privacy-first experimentation platform

> A portfolio write-up of how I designed and built an A/B-testing platform whose AI agents do
> the repetitive parts of a data scientist's job on top of a statistics engine you can actually
> trust. Written in the voice of the engineer/DS who built it. The working code, tests, and a
> runnable demo are in this repository.

## 1. The problem
At scale, experimentation is gated by a few experienced data scientists. The work that
consumes them is high-skill but highly patterned: turning a fuzzy hypothesis into a sound
design, choosing the OEC and guardrails, sizing the test, watching it for data bugs, running
the *correct* statistical test, and writing a readout a PM can act on. Most "A/B tools" stop at
feature flags + a naive z-test and leave the rigor — and the interpretation — to humans who
don't scale.

**Thesis:** that patterned work is exactly what a *grounded* AI agent can do — if it is forced
to call a real statistics engine instead of guessing. So I built a serious experimentation
engine and wrapped it in AI agents that operate it through the same audited tools a human would.

## 2. What I built
A working platform (this repo) that runs the full loop end-to-end:

**create → assign → ingest → analyze → results → dashboard**, plus a grounded agent layer.

- **Deterministic assignment** — pure 64-bit hash bucketing with targeting, traffic gating,
  layers (mutual exclusion), holdouts, and cross-experiment orthogonality; identical in the
  server and the Python/TypeScript SDKs (pinned by shared golden fixtures).
- **Privacy-first ingestion** — pseudonymous units only; a PII guard + a per-workspace event
  allow-list reject anything personal *before* it reaches storage; analytics run on DuckDB
  locally and on the customer's warehouse in production (raw data never leaves their perimeter).
- **A real statistics engine** (see §4).
- **An analysis pipeline + REST API + a Next.js dashboard** that lead with confidence intervals
  and flag data-quality problems loudly.
- **A grounded AI agent foundation** (see §5).
- **Multi-tenancy, RBAC, audit logging, and API keys** for a real SaaS.

It is tested: **90 backend tests + 28 SDK + frontend component tests**, `ruff` + `mypy --strict`
clean, CI on every push. A single command — `make demo` — runs the whole thing on in-memory
stores with no external services.

## 3. What the demo shows
`make demo` seeds two experiments with known ground truth and runs the real pipeline:

- **A winning experiment** ("new checkout"): treatment 14.2% vs control 10.7% →
  **+3.5pp absolute, +33% relative lift, 95% CI [+2.6pp, +4.4pp], p ≈ 5e-14 → SIGNIFICANT**,
  and a Bayesian **P(treatment better) = 100%** with negligible expected loss.
- **A broken experiment** ("banner color"): an injected allocation skew is caught as a
  **Sample Ratio Mismatch (χ² ≈ 1143, p ≈ 1e-250)** and the readout says *"results NOT
  trustworthy"* — the single most important thing a real platform must do and most don't.
- **Power**: 3,841 units/arm to detect a +2pp lift on a 10% baseline (α=0.05, power=0.8).

Every number is computed by the deterministic engine — none is produced by an LLM.

## 4. The statistics (where credibility is won or lost)
I implemented the methods that naive tools get wrong, and I *proved* they're right.

- **Correct tests per metric type:** two-proportion z-test (pooled) with a Wald CI; Welch's
  t-test for means.
- **Delta method** for the relative-lift CI (a ratio of random quantities) — the #1 silent
  source of false positives when the analysis unit differs from the randomization unit.
- **CUPED** variance reduction (`θ = Cov(Y,X)/Var(X)`): tighter CIs for the same users.
- **Sequential / always-valid inference** so peeking at the dashboard does not inflate the
  false-positive rate — making the *easy* path the *correct* one.
- **Bayesian** analysis: P(treatment > control) and expected loss for a clean decision rule.
- **SRM** (chi-square) checked **first**; **multiple-comparison correction** (Bonferroni / Holm /
  Benjamini–Hochberg) across the metric family; **power/MDE** sizing.

**How I know it's correct** (this is the part I'd want a reviewer to see):
- Cross-checked against `scipy` and `statsmodels` on worked examples.
- **A/A calibration by simulation:** over hundreds of null experiments the p-values are
  ~uniform and the false-positive rate ≈ α.
- A **power simulation** confirms the sample-size formula achieves the target power.
- The delta-method variance is validated against a bootstrap.

The engine is **pure** (no I/O) and consumes only *sufficient statistics* (counts, sums,
sums-of-squares, covariances), so it is unit-testable, deterministic, and portable to any
warehouse with one group-by per metric.

## 5. Grounded AI — using an LLM for statistics without it hallucinating
The agents never compute or invent a number. They call the engine through typed **tools** and
narrate the results; a **grounding check** parses every number in an agent's output and asserts
it traces to a recorded tool result, and the full tool-call trace is persisted (`agent_run` /
`agent_step`) for audit. The agent layer is provider-neutral and fully tested against a **mock
model** (no API key), including a test that a deliberately invented number is caught.

This is the defensible answer to "why trust an LLM with statistics?": *we don't — we trust the
engine, and the LLM operates it, on the record.* Decisions stay human: agents propose designs,
raise alerts, and recommend ship/no-ship; people approve.

## 6. Privacy-first, by construction
This is a genuine design constraint, not a checkbox: pseudonymous units; a typed, allow-listed
event schema; an ingestion PII guard that rejects emails/phones/IPs with a reason; no PII in the
analytics store (asserted by tests); warehouse-native analytics so raw data can stay in the
customer's perimeter; and an immutable audit trail. It de-risks GDPR/CCPA and aligns with a
privacy-focused buyer's values.

## 7. Architecture & engineering
Python 3.12 / FastAPI / Pydantic v2 / SQLModel + Alembic for the API and metadata (Postgres);
NumPy/SciPy/statsmodels for stats; DuckDB (→ warehouse) for analytics; Next.js + TypeScript +
Tailwind for the dashboard; the Anthropic API for the agents. Clean separation: a pure stats
engine, a thin analytics adapter (sufficient-statistics interface), thin API handlers over
domain services, and the agent layer on top. Multi-tenant from day one (`org_id` everywhere).

## 8. Honest limitations / what's next
- The concrete agents (Designer/Monitor/Analyst/Readout) are built on the foundation but need a
  live model key to run; the foundation and grounding are done and tested.
- Ratio metrics and CUPAC are scoped but not fully wired into the API yet.
- One warehouse connector (DuckDB) is implemented; BigQuery/Snowflake are adapter swaps.
- Sequential inference implements one always-valid method; group-sequential boundaries are a
  documented next step.

## 9. What I'd want you to take from this
I can design experimentation infrastructure that is **statistically correct and provably so**,
**privacy-first by construction**, and that uses **LLMs safely** by grounding them in a
deterministic engine — shipped as clean, tested, multi-tenant code with a runnable demo.

*Plan and rationale: [`docs/`](.); build steps: [`prompts/`](../prompts/); run it: `make demo`.*
