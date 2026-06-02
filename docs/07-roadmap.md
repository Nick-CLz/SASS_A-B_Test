# 07 — Roadmap

Each milestone is independently demoable. Each maps to one or more build prompts in
[`prompts/`](../prompts/). Build in order; don't start a milestone until the previous one's
acceptance criteria pass.

## M0 — Scaffold & tooling  → `P01`
Repo, Python + Node toolchains, lint/format/type/test wired, CI green on an empty app, docker
compose up. **Demo:** `pytest` and `pnpm test` run; `GET /v1/health` returns ok.

## M1 — Experiment engine  → `P02`, `P03`, `P04`, `P05`
Core data model + experiment/variant/metric CRUD + deterministic assignment (layers, holdouts,
targeting, ramp) + Python & TS SDKs.
**Demo:** create an experiment via API; `get_variant` returns stable, correctly-split variants;
assignment golden tests pass; orthogonality + exclusivity proven.

## M2 — Data + frequentist stats  → `P06`, `P07`
Event ingestion (PII guard + allow-list) into DuckDB; analytics adapter computes sufficient
stats; frequentist engine (z/Welch, CIs, relative lift via delta method), SRM, power/MDE.
**Demo:** ingest synthetic events; `analyze` returns effects + CIs + SRM + significance;
A/A calibration test passes (uniform p-values).

## M3 — Dashboard  → `P09`, `P10`
Next.js UI: experiment list/detail, config, live results with CIs/significance, SRM banner,
power calculator.
**Demo:** the whole M2 flow is visible and explorable in the browser.

## M4 — Advanced stats  → `P08`
CUPED variance reduction, sequential/always-valid inference, Bayesian (P(better) + expected
loss), multiple-comparison correction, segment breakdowns.
**Demo:** toggle CUPED and watch CIs tighten; peek safely with sequential intervals; Bayesian
view; segment explorer with correction.

## M5 — AI agents  → `P11`, `P12`, `P13`, `P14`
Agent foundation (tool framework + tracing + model routing + caching), then Designer, Monitor,
Analyst, Readout. Grounding + eval harness.
**Demo:** hypothesis → Designer drafts a powered experiment → inject an SRM bug → Monitor flags
it → Analyst runs sequential+CUPED → Readout writes a sourced ship/no-ship. Every number traces
to a tool call.

## M6 — SaaS hardening  → `P15`
Multi-tenancy (org/workspace isolation), auth, RBAC, API keys, audit log, rate limiting.
**Demo:** two orgs can't see each other's data; roles enforced; audit trail complete.

## M7 — Polish, demo & deploy  → `P16`
Seeded demo dataset + scripted demo, deployment (container host), the written case study
(the DuckDuckGo-facing artifact), README/marketing pass.
**Demo:** one command spins up a fully seeded, deployable instance; the case study reads like a
senior DS wrote it.

## Two finish lines (pick where to stop for each audience)
- **DuckDuckGo / portfolio:** ship through **M5** + the M7 case study. The story is rigor +
  privacy + grounded AI. Multi-tenancy/billing optional.
- **Sellable SaaS:** continue through **M6** and the deploy/onboarding parts of **M7**, then add
  billing and onboarding (post-roadmap).

## Sequencing notes
- The dashboard (M3) can begin in parallel once the results API (end of M2) is stable.
- The agent layer (M5) depends on the stats engine being solid (M2/M4) because agents are only
  as trustworthy as the tools they call.
- Keep `org_id` on every tenant-scoped table from M1 so M6 is auth+filtering, not a migration.

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| Stats subtly wrong | calibration/A-A tests in CI; cross-check vs scipy/statsmodels |
| Agents hallucinate numbers | grounding test in eval harness; full tool-call traces |
| Scope creep | strict milestone acceptance criteria; stretch items clearly tagged |
| Cost of agent runs | model routing + prompt caching + token budgets from day one |
| Privacy regressions | PII-guard tests assert no PII reaches storage |
