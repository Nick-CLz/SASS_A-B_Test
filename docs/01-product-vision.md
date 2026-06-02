# 01 — Product vision

## Problem
At scale, experimentation is a bottleneck. A handful of experienced data scientists gate
hundreds of experiments. The work that consumes them is patterned and repetitive:
- translating a fuzzy product hypothesis into a *sound* experiment design;
- choosing the success metric, the guardrails, and a defensible sample size;
- babysitting the experiment for data-quality bugs (the #1 cause of wrong conclusions);
- running the *correct* statistical test (most teams quietly get this wrong — peeking,
  ignoring ratio-metric variance, no multiple-comparison control);
- writing a readout that a PM can actually act on.

Most "A/B testing tools" stop at feature flags + a naive z-test. The rigor and the
interpretation — the actual data-science — are left to humans who don't scale.

## Our answer
Automate the patterned work with **grounded AI agents** sitting on top of a **serious
statistics engine**, and keep humans for judgment and approvals. The agent proposes; the
human disposes.

## Target users (personas)
1. **Priya — Staff Data Scientist (the buyer's champion).** Wants rigor enforced by default
   and her time freed from readouts. Judges us on whether the stats are correct and the
   agent's reasoning is sound. *She is also the DuckDuckGo-interview persona.*
2. **Marco — Product Manager.** Wants to launch an experiment without a DS babysitting every
   step, and wants a readout in plain language with a clear recommendation.
3. **Dana — Data/Platform Engineer.** Wants assignment to be fast and deterministic, events
   easy to send, and the analytics to run on the company's own warehouse.
4. **Sam — Eng/Data leadership (economic buyer).** Wants more experiments per DS, fewer bad
   launches, and an auditable trail. Cares about privacy/compliance risk.

## Value proposition
- **For DS teams:** 5–10× more experiments analyzed per data scientist, with the rigor
  *increased*, not lowered, because the engine enforces correct method and the agent explains
  it.
- **For PMs:** self-serve a well-designed experiment and get a trustworthy, plain-language
  readout.
- **For leadership:** fewer wrong "ship" decisions, a full audit trail, and lower privacy
  risk.

## Privacy-first as a product principle (not a checkbox)
This is both a genuine differentiator and the strongest signal for a privacy-focused
employer/buyer.
- **Pseudonymous units only.** The randomization/analysis unit is an opaque ID. No emails,
  names, phone numbers, precise geolocation, or raw IPs enter the event stream or analytics
  store.
- **Data minimization.** Event properties are typed and allow-listed per project; free-text
  is discouraged and never required for the core stats.
- **Self-host / warehouse-native.** Sensitive customers can run the analytics on their own
  warehouse so raw data never leaves their perimeter. → [`02-architecture.md`](./02-architecture.md)
- **PII guard in the pipeline.** Ingestion runs a configurable detector that rejects or
  redacts fields that look like PII, and the test suite asserts no PII reaches storage.
- **Auditability.** Every agent action and every experiment decision is logged immutably.
- **Differential-privacy-ready (stretch).** The aggregation layer is designed so DP noise
  can be added to released metrics later without re-architecting.

## Scope: in vs. out
**In scope (build):**
- Experiment lifecycle: design → review → ramp → monitor → analyze → decide → archive.
- Deterministic assignment with layers, holdouts, targeting, gradual ramp.
- Event ingestion + warehouse-native analytics (DuckDB locally).
- Statistics: frequentist + Bayesian + sequential, CUPED, SRM, power/MDE, segments.
- AI agents: Designer, Health Monitor, Analyst, Readout Writer (+ Reviewer, Memory as stretch).
- Dashboard, REST API, Python + TS SDKs.
- Multi-tenancy, auth, RBAC, audit (SaaS phase).

**Out of scope (at least initially):**
- Visual/WYSIWYG page editor (Optimizely-style). We're an *engine + brain*, not a page builder.
- Mobile SDKs beyond a thin client (web/server first).
- Real-time sub-second streaming analytics (batch micro-windows are enough to start).
- Billing/payments integration (design for it; don't build it in the MVP).

## Product principles
1. **Correct-by-default.** The easy path is the statistically sound path. Peeking is safe
   because sequential inference is the default for monitoring.
2. **Grounded AI.** Agents never produce a number they didn't get from the engine. Every
   claim is traceable to a tool call.
3. **Human-in-the-loop for decisions.** Agents draft designs, raise alerts, and recommend
   ship/no-ship; humans approve launches, pauses, and ships.
4. **Boring infrastructure, exciting brain.** The engine is deterministic, tested, and dull
   on purpose. The intelligence lives in the agent layer.
5. **Explain everything.** Every result links to its method, assumptions, and caveats.

## What "done" looks like for the demo
A reviewer can: create an experiment from a one-paragraph hypothesis (Designer agent fills the
config), send synthetic events, watch the Monitor agent flag an injected SRM bug, let the
Analyst run sequential + CUPED analysis, and read a generated, sourced ship/no-ship readout —
all with no PII anywhere, and every number traceable to a tool call.
