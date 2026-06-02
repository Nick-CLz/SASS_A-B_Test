# Build prompts

This folder is **the build, broken into runnable steps**. Each `P##` file is a self-contained
prompt you hand to a (cheaper) model. They're ordered; run them in sequence. Every prompt:
- points at the `docs/` it depends on (docs are the source of truth),
- lists concrete deliverables,
- ends with **acceptance criteria** (testable),
- tells the model to **commit when its tests pass**.

**Start here:** read [`00-prompting-guide.md`](./00-prompting-guide.md) — it covers how to drive
the build, the conventions every prompt assumes, and **which model to use for which prompt**
(your cost lever).

## Order
| # | Prompt | Milestone | Suggested model |
|---|---|---|---|
| P01 | [Scaffold & tooling](./P01-scaffold-and-tooling.md) | M0 | small |
| P02 | [Core data model](./P02-core-data-model.md) | M1 | medium |
| P03 | [Experiment CRUD API](./P03-experiment-crud-api.md) | M1 | medium |
| P04 | [Assignment engine](./P04-assignment-engine.md) | M1 | **large** (correctness-critical) |
| P05 | [SDKs (Python + TS)](./P05-sdks.md) | M1 | medium |
| P06 | [Event ingestion + DuckDB](./P06-ingestion-duckdb.md) | M2 | medium |
| P07 | [Stats engine — frequentist](./P07-stats-frequentist.md) | M2 | **large** (correctness-critical) |
| P08 | [Stats engine — advanced](./P08-stats-advanced.md) | M4 | **large** (correctness-critical) |
| P09 | [Results & analysis API](./P09-results-api.md) | M2/M3 | medium |
| P10 | [Dashboard (Next.js)](./P10-dashboard.md) | M3 | medium |
| P11 | [Agent foundation](./P11-agent-foundation.md) | M5 | **large** |
| P12 | [Designer agent](./P12-agent-designer.md) | M5 | medium |
| P13 | [Monitor agent](./P13-agent-monitor.md) | M5 | medium |
| P14 | [Analyst + Readout agents](./P14-agent-analyst-readout.md) | M5 | medium |
| P15 | [Multi-tenancy, auth, RBAC, audit](./P15-saas-hardening.md) | M6 | medium |
| P16 | [Demo data, deploy, case study](./P16-demo-deploy-casestudy.md) | M7 | medium |

"small/medium/large" map to `AGENT_MODEL_SMALL/MEDIUM/LARGE` in `.env.example`. Correctness-
critical prompts (assignment, stats) are worth a larger model even on a tight budget — a bug
there invalidates every result. See the guide for the full rationale.

## Tips
- Run one prompt per session/context to keep the model focused.
- After each prompt, skim the diff and run the acceptance checks yourself before moving on.
- If a prompt is too big for your chosen model, each has a "If you must split this" note.
