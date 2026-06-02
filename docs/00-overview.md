# 00 — Overview

**Read this first.** It frames the whole plan in two pages. Every other doc expands one part
of what's here.

## One sentence
Mallard is an **AI-native, privacy-first A/B testing platform** where AI agents do the
repetitive parts of a data scientist's job — designing experiments, monitoring their health,
running the statistics, and writing the readout — while a human approves the decisions.

## The thesis
Running experiments well at a large company is mostly *not* glamorous modeling. It is:
designing a sound experiment, picking the right metrics, sizing it, watching it for data
bugs, running the correct statistical test, and writing a clear readout that a PM can act on.
That work is **high-skill but highly patterned** — which is exactly what a well-grounded AI
agent can do, *if* it is forced to call a real statistics engine instead of guessing.

Mallard is built around that idea: a serious experimentation engine, wrapped in AI agents
that operate it. The agents are the product's headline; the engine is what makes them
trustworthy.

## The two audiences (and why one codebase serves both)
- **Portfolio / interview piece** (e.g. for a privacy-focused company like DuckDuckGo):
  shows statistical depth, clean engineering, a privacy-first stance, a great demo, and a
  written case study. Weighted toward rigor and storytelling.
- **Sellable SaaS** (data-science / growth teams at larger companies): multi-tenant,
  real assignment engine, warehouse-native analytics, governance, AI agents as the
  differentiator. Weighted toward product completeness.

These don't conflict. The same engine + agents serve both; only the *emphasis* of the demo
and the surrounding collateral differ. See [`08-go-to-market.md`](./08-go-to-market.md).

## The four pillars
1. **AI-native** — agents design / monitor / analyze / write up. Grounded: they call tools,
   never invent numbers. → [`05-ai-agents.md`](./05-ai-agents.md)
2. **Privacy-first** — pseudonymous units, no PII in the pipeline, self-host option.
   → [`01-product-vision.md`](./01-product-vision.md)
3. **Statistically serious** — frequentist + Bayesian + sequential, CUPED, SRM, power.
   → [`04-statistics-engine.md`](./04-statistics-engine.md)
4. **Warehouse-native option** — DuckDB for the demo, warehouse connectors for production.
   → [`02-architecture.md`](./02-architecture.md)

## The system in one diagram
```
                         ┌───────────────────────────────────────────────┐
                         │                  Mallard                        │
   client apps           │                                                 │
  ┌──────────┐  assign   │   ┌─────────────┐      ┌──────────────────┐     │
  │  web/app │──────────▶│   │ Assignment  │      │   Experiment      │     │
  │  + SDK   │  exposure │   │  service    │◀────▶│   management API  │     │
  └────┬─────┘  + events │   │ (bucketing) │      │ (Postgres)        │     │
       │                 │   └─────────────┘      └─────────┬────────┘     │
       │  events         │          ▲                       │              │
       └────────────────▶│   ┌──────┴───────┐      ┌────────▼────────┐     │
                         │   │ Event        │─────▶│  Analytics store │     │
                         │   │ ingestion    │      │  (DuckDB / WH)   │     │
                         │   └──────────────┘      └────────┬────────┘     │
                         │                                  │              │
                         │   ┌──────────────┐      ┌────────▼────────┐     │
                         │   │  AI agents   │◀────▶│  Statistics      │     │
                         │   │ (Claude)     │ tools│  engine (pure)   │     │
                         │   └──────┬───────┘      └─────────────────┘     │
                         │          │ readouts, designs, alerts            │
                         │   ┌──────▼───────────────────────────────┐     │
                         │   │  Dashboard (Next.js)                  │     │
                         │   └───────────────────────────────────────┘     │
                         └───────────────────────────────────────────────┘
```

## What gets built, in order
A condensed map (full version in [`07-roadmap.md`](./07-roadmap.md); each maps to a prompt
in [`prompts/`](../prompts/)):

| Milestone | What works at the end | Prompts |
|---|---|---|
| **M0 Scaffold** | repo, tooling, CI, docker | P01 |
| **M1 Engine** | create experiments; deterministic assignment; SDK | P02–P05 |
| **M2 Data + stats** | ingest events; frequentist results + SRM + power | P06–P07 |
| **M3 Dashboard** | see experiments and results in the UI | P09–P10 |
| **M4 Advanced stats** | CUPED, sequential, Bayesian, segments | P08 |
| **M5 AI agents** | designer, monitor, analyst, readout writer | P11–P14 |
| **M6 SaaS** | multi-tenant, auth, RBAC, audit | P15 |
| **M7 Polish** | demo data, deploy, case study | P16 |

## How to read the rest
- Product & users → [`01-product-vision.md`](./01-product-vision.md)
- How it's built → [`02-architecture.md`](./02-architecture.md)
- The schema → [`03-data-model.md`](./03-data-model.md)
- The math → [`04-statistics-engine.md`](./04-statistics-engine.md)
- The agents → [`05-ai-agents.md`](./05-ai-agents.md)
- API & SDK → [`06-api-and-sdk.md`](./06-api-and-sdk.md)
- Plan & sequencing → [`07-roadmap.md`](./07-roadmap.md)
- Business → [`08-go-to-market.md`](./08-go-to-market.md)
- Terms → [`09-glossary.md`](./09-glossary.md)
- Why these choices → [`10-decisions.md`](./10-decisions.md)
