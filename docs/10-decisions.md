# 10 — Decisions (ADR-style)

Why the project is the way it is. Each decision lists the choice, the rationale, alternatives,
and how to revisit it. Add new ADRs at the bottom as the build proceeds.

## D1 — Tech stack: FastAPI + Next.js + Postgres + DuckDB + Claude
**Choice:** Python/FastAPI backend & stats; Next.js/TS dashboard; Postgres metadata; DuckDB
analytics (→ warehouse connectors); Claude for agents.
**Why:** Python is the lingua franca of data science (scipy/statsmodels/pandas) — credible for
the audience and natural for the stats engine. DuckDB gives zero-infra, fast, warehouse-shaped
analytics for the demo and a clean adapter path to real warehouses. Next.js/TS is the standard
for a polished dashboard. Claude for grounded tool-use agents.
**Alternatives:** all-Python + Streamlit (faster, less polished — rejected for the
portfolio/SaaS polish bar); Node full-stack (weaker stats story). 
**Revisit if:** the team is TS-only, or a specific warehouse is mandated day one.

## D2 — Stats engine is pure and consumes only sufficient statistics
**Why:** purity → unit-testable against textbook fixtures and calibratable via simulation;
sufficient-stats interface → analysis is one group-by per metric, cheap and **warehouse-native**,
and the same engine can be a tool the agents call.
**Alternatives:** stats computed inline in API handlers (untestable, not reusable — rejected).
**Revisit if:** a method genuinely needs row-level data (then add a narrow, explicit path).

## D3 — AI agents are grounded: they never compute statistics
**Why:** eliminates the fatal failure mode of LLM-stats products (hallucinated p-values); makes
output auditable (every number traces to a tool call); is the credible answer to "why trust an
LLM here?".
**Alternatives:** let the LLM reason over raw numbers (rejected — uncalibrated, unauditable).
**Revisit:** never for the core numbers; narrative/qualitative synthesis stays the LLM's job.

## D4 — Privacy-first by construction, not policy
**Choice:** pseudonymous units, typed allow-listed events, ingestion PII guard, no PII in the
analytics store, self-host/warehouse-native option, immutable audit.
**Why:** genuine differentiator; de-risks GDPR/CCPA; strongest signal for a privacy-focused
audience; warehouse-native means raw data needn't leave the customer.
**Revisit if:** a customer segment needs richer (consented) attributes — add behind explicit
consent + DP, never by loosening the default.

## D5 — Warehouse-native via an analytics adapter (DuckDB default)
**Why:** matches where the market is moving (compute on the customer's warehouse); DuckDB makes
the demo instant and local while the adapter keeps BigQuery/Snowflake/Databricks a config swap.
**Alternatives:** ship our own columnar store (heavy), or Postgres-only analytics (won't scale).

## D6 — Multi-tenancy modeled from day one, enforced in M6
**Choice:** `org_id`/`workspace_id` on every tenant-scoped table from M1; auth/RBAC enforcement
lands in M6.
**Why:** avoids a painful migration; lets the MVP move fast without a half-built auth system,
while keeping the SaaS path open.

## D7 — Human-in-the-loop for decisions
**Choice:** agents propose/monitor/analyze/recommend; humans approve launch, pause, ship.
**Why:** correct product stance for high-stakes decisions; builds trust; reduces blast radius of
agent error. (Auto-pause on severe guardrail breach is a configurable policy, not a default.)

## D8 — Sequential inference is the default for monitoring
**Why:** people peek; fixed-horizon tests punish peeking with false positives. Making the live
view always-valid makes the *easy* path the *correct* path (product principle: correct-by-default).

## D9 — Model identifiers are configuration, with routing by difficulty
**Why:** lets the planned cost-optimization pass re-route freely (Haiku/Sonnet/Opus) without
code changes; pairs with prompt caching, token budgets, and batch for healthy margins/COGS.

## D10 — Build executed prompt-by-prompt by a cheaper model
**Why:** the user's explicit workflow — expensive model for architecture (this plan), cheap
model for execution. Hence the self-contained, acceptance-criteria-driven prompts in
[`prompts/`](../prompts/) and the docs-as-source-of-truth rule.

## D-Naming — Working title "Mallard"
**Choice:** "Mallard" as a placeholder (duck nod to DuckDB; brandable). **This is the one place
to change the name.** When you rename, update: root `README.md` title, `LICENSE` holder,
`CLAUDE.md`, package names in `backend/`/`frontend/` (set in P01/P10), and the dashboard header.
**Open:** final product name + the open-core vs. proprietary license decision (see
[`08-go-to-market.md`](./08-go-to-market.md)) — decide before any public release.

---
### Open questions to resolve during the build
- Which sequential method to implement first (mSPRT vs. group-sequential)? → start with one
  always-valid confidence sequence; document the choice in an ADR here.
- First warehouse connector to build after DuckDB (BigQuery vs. Snowflake)? → driven by the
  first real customer / target employer's stack.
- Final license (open-core vs. proprietary)? → before first public push.
