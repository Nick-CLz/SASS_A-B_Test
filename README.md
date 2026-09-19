# Mallard — AI-native, privacy-first experimentation platform

> **Working title:** "Mallard" (a nod to DuckDB / the duck heritage). It's a placeholder —
> rename it in one place later (`docs/10-decisions.md` → "Naming"). Pick the name you like.

Mallard is an **A/B testing & experimentation platform** built for data-science teams
operating at scale in large companies. Its differentiator: **AI agents that take over the
repetitive parts of the data scientist's job** — designing experiments, watching their
health, running the statistics, and writing the ship / no-ship readout — while keeping a
human in the loop for decisions.

This repository is, first, a **complete plan**. The high-value architecture and the
statistics were designed here; the actual build is meant to be executed prompt-by-prompt by
a cheaper model (see [`prompts/`](./prompts/)). That split is deliberate: expensive model
for design, cheap model for execution.

---

## Why this exists (the two audiences)

This project is built to serve two goals at once. Both are legitimate and the architecture
serves both — see [`docs/08-go-to-market.md`](./docs/08-go-to-market.md).

1. **A portfolio / interview piece** for a privacy-focused company (e.g. DuckDuckGo).
   The emphasis there is statistical rigor, clean code, a privacy-first design, a
   compelling live demo, and a written case study that reads like a senior data
   scientist wrote it.
2. **A sellable SaaS product** for data-science / growth teams at larger companies.
   The emphasis there is multi-tenancy, a real assignment engine, warehouse-native
   analytics, governance, and the AI-agent layer as the headline feature.

## What makes it different

| Pillar | What it means | Why it matters |
|---|---|---|
| **AI-native** | Agents design, monitor, analyze, and write up experiments. They *call* the stats engine as tools — they never invent numbers. | This is the "AI takes over the DS workflow" thesis. Grounded, auditable, trustworthy. |
| **Privacy-first** | Pseudonymous units, no PII in the event stream, data minimization, self-host option. | Aligns with privacy-focused buyers (and DuckDuckGo's values); de-risks GDPR/CCPA. |
| **Statistically serious** | Frequentist + Bayesian + sequential ("peek any time") inference, CUPED variance reduction, SRM detection, power analysis. | Credibility with real DS teams; this is where most cheap tools are weak. |
| **Warehouse-native option** | DuckDB embedded for the demo; connectors to Snowflake / BigQuery / Databricks for production. | Compute on the customer's own data — the direction the market is moving. |

## Tech stack (decided)

- **Backend & stats:** Python 3.12, FastAPI, Pydantic v2, SQLModel/SQLAlchemy, Alembic,
  NumPy / SciPy / statsmodels, pandas.
- **Analytics engine:** DuckDB (embedded; attaches Parquet, scales out to MotherDuck /
  warehouse connectors later).
- **Metadata store:** PostgreSQL.
- **AI layer:** Anthropic Claude API (model routing across Haiku / Sonnet / Opus, tool use,
  structured outputs, prompt caching).
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts +
  TanStack Query.
- **SDKs:** Python + TypeScript client libraries over a documented REST API.
- **Infra:** Docker + docker-compose locally; GitHub Actions CI; deploy to Fly.io / Render
  (or any container host) later.

Full rationale (and the alternatives considered) is in
[`docs/10-decisions.md`](./docs/10-decisions.md).

## Repository layout

```
.
├── README.md                ← you are here
├── CLAUDE.md                ← context & conventions for the agent doing the build
├── docs/                    ← the plan (source of truth)
│   ├── 00-overview.md
│   ├── 01-product-vision.md
│   ├── 02-architecture.md
│   ├── 03-data-model.md
│   ├── 04-statistics-engine.md
│   ├── 05-ai-agents.md
│   ├── 06-api-and-sdk.md
│   ├── 07-roadmap.md
│   ├── 08-go-to-market.md
│   ├── 09-glossary.md
│   └── 10-decisions.md
├── prompts/                 ← the build, one runnable prompt at a time
│   ├── README.md
│   ├── 00-prompting-guide.md
│   └── P01 … P16 …
├── backend/                 ← FastAPI app + stats engine + agents (built by prompts)
├── frontend/                ← Next.js dashboard (built by prompts)
├── sdks/                    ← Python + TS client SDKs (built by prompts)
└── infra/                   ← docker-compose, CI, deploy configs
```

## How to use this repository

1. **Read the plan.** Start at [`docs/00-overview.md`](./docs/00-overview.md) and skim
   through `10-decisions.md`. This is the shared source of truth every build prompt points
   back to.
2. **Run the build.** Open [`prompts/00-prompting-guide.md`](./prompts/00-prompting-guide.md),
   then feed prompts `P01`, `P02`, … to your chosen (cheaper) model one at a time. Each
   prompt is self-contained, ends with explicit acceptance criteria, and tells the model to
   commit when its tests pass.
3. **Optimize cost.** The prompting guide has a section on model routing (which prompts can
   run on a small model vs. which deserve a bigger one) so your follow-up cost pass has a
   head start.

## Status

✅ **Built and runnable through milestone M7** (everything that doesn't need a model key).
Done: the core platform (data model · deterministic assignment + `/v1/assign` · Python/TS SDKs
with cross-language golden-fixture parity), privacy-first ingestion + DuckDB analytics, the full
**statistics engine** (frequentist + CUPED + sequential + Bayesian + SRM + power), the analysis
pipeline + REST API, a Next.js **dashboard**, the **grounded AI-agent foundation** (tools + a
"never invents numbers" check + persisted traces, mock-tested), and **SaaS hardening** (RBAC,
tenant isolation, audit log, API keys). Backend is `ruff` + `mypy --strict` + `pytest` green
(**90 tests**); frontend + SDK suites green; CI wired.

**Try it:**
- `make demo` — the whole pipeline in one command, no setup ([what you'll see](./docs/case-study.md#3-what-the-demo-shows)).
- **[`docs/USAGE.md`](./docs/USAGE.md)** — drive a real experiment yourself via the API + dashboard.
- **[`docs/case-study.md`](./docs/case-study.md)** — the senior-DS write-up.
- `make setup && make test` — verify locally.

**Remaining:** the concrete AI agents (Designer / Monitor / Analyst / Readout) — built on the
tested foundation; running them live needs `ANTHROPIC_API_KEY`.

## License

See [`LICENSE`](./LICENSE). Currently "all rights reserved" while the product/business model
is decided; `docs/08-go-to-market.md` discusses an open-core alternative.
