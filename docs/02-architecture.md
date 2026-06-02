# 02 — Architecture

## Components
```
┌────────────┐   ┌──────────────────────────────────────────────────────────┐
│  SDKs       │   │  Backend (FastAPI, Python 3.12)                            │
│  py / ts    │──▶│                                                            │
└────────────┘   │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
                 │  │ API layer   │  │ Assignment   │  │ Ingestion          │ │
┌────────────┐   │  │ (/v1 REST)  │  │ engine       │  │ (events→analytics) │ │
│ Dashboard   │──▶│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘ │
│ (Next.js)   │   │         │                │                    │            │
└────────────┘   │  ┌──────▼────────────────▼────────────────────▼─────────┐  │
                 │  │ Domain services (experiments, metrics, results, org)  │  │
                 │  └──────┬───────────────────────────┬────────────────────┘ │
                 │         │                            │                       │
                 │  ┌──────▼──────┐            ┌────────▼─────────┐            │
                 │  │ Stats engine│◀───tools───│ Agent layer       │            │
                 │  │ (pure, py)  │            │ (Claude API)      │            │
                 │  └──────┬──────┘            └───────────────────┘            │
                 └─────────┼──────────────────────────────────────────────────┘
            ┌──────────────┼───────────────┐
            ▼                              ▼
   ┌──────────────┐              ┌──────────────────────┐
   │ Postgres      │              │ Analytics engine      │
   │ (metadata:    │              │ DuckDB (local) →      │
   │ experiments,  │              │ BigQuery/Snowflake/   │
   │ orgs, results)│              │ Databricks (prod)     │
   └──────────────┘              └──────────────────────┘
```

### 1. API layer (`backend/app/api`)
Versioned REST under `/v1`, generated OpenAPI. Thin: validates input (Pydantic), calls a
domain service, returns a typed response. Auth middleware (stubbed in MVP, real in M6). See
[`06-api-and-sdk.md`](./06-api-and-sdk.md).

### 2. Assignment engine (`backend/app/assignment`)
Pure, deterministic bucketing. Given `(unit_id, experiment, attributes)` it returns a variant
(or "not eligible"). Stateless and fast; no DB call on the hot path (config is cached). Details
and the hashing algorithm: [`04-statistics-engine.md`](./04-statistics-engine.md#assignment)
and [`03-data-model.md`](./03-data-model.md).

### 3. Ingestion (`backend/app/ingestion`)
Receives exposure + metric events from SDKs, runs the **PII guard**, validates against the
project's allow-listed event schema, and writes to the analytics engine. Batch-friendly. For
the MVP this is a synchronous HTTP endpoint writing to DuckDB; the interface is designed so a
queue (Redis/Kafka) and a warehouse loader can be slotted in without touching callers.

### 4. Analytics engine (`backend/app/analytics`) — warehouse-native by design
A thin **adapter interface** (`AnalyticsBackend`) with one method family: "give me the
aggregates the stats engine needs" (per-variant counts, sums, sums-of-squares, covariances
for CUPED, per-day series, per-segment slices). Two implementations:
- **DuckDB** (default, local/demo): embedded, fast, reads Parquet, zero infra. *This is the
  "Duck" in the stack and the cute nod to DuckDB/DuckDuckGo.*
- **Warehouse** (prod): the same SQL templated for BigQuery / Snowflake / Databricks so
  computation runs *in the customer's warehouse* and raw data never leaves their perimeter.

Because the stats engine only ever consumes **sufficient statistics** (counts, sums,
sums-of-squares, covariances), the analytics layer can compute those with a single
group-by-per-metric query — cheap and warehouse-friendly.

### 5. Statistics engine (`backend/app/stats`) — pure and deterministic
No I/O, no globals, no network. Input: sufficient statistics (NumPy arrays / dataclasses).
Output: estimates, intervals, p-values, diagnostics. This purity is what makes it
unit-testable against textbook fixtures and what lets the agents *call it as tools*. Full
method list: [`04-statistics-engine.md`](./04-statistics-engine.md).

### 6. Agent layer (`backend/app/agents`)
Claude-powered agents (Designer, Monitor, Analyst, Readout). Each is a system prompt + a set
of **tools** that wrap domain services and the stats engine. The agent orchestrates and
narrates; the tools do the work. Grounding, routing, caching, and evals:
[`05-ai-agents.md`](./05-ai-agents.md).

### 7. Dashboard (`frontend/`)
Next.js App Router + TS. Lists experiments, shows config, live health, results with CIs and
significance, segment explorer, and the agent-written readout. Talks only to `/v1`.

## Data stores
| Store | Holds | Why |
|---|---|---|
| **Postgres** | experiments, variants, metrics, orgs/users, analysis runs, results, agent runs, audit log | relational metadata, transactions, RBAC |
| **Analytics engine (DuckDB → warehouse)** | exposure + metric events, computed aggregates | columnar, cheap aggregation, warehouse-native option |

Metadata and event data are deliberately separated: metadata is small/relational/transactional;
event data is large/append-only/columnar. Results (small, computed) live back in Postgres so the
dashboard and audit trail are simple.

## Request flows
**Assign:** SDK → `POST /v1/assign` → assignment engine (cached config) → variant. SDK logs an
**exposure** event. *Analysis only counts exposed/triggered units* (avoids dilution).

**Track:** SDK → `POST /v1/events` (batched) → PII guard + schema validation → analytics engine.

**Analyze:** scheduler or user/agent → analytics engine computes sufficient stats → stats engine
computes results → results stored in Postgres → dashboard/agent read them.

**Agent readout:** Analyst agent calls `run_analysis` tool → gets results from the stats engine →
calls `check_srm`, `segment_breakdown` tools → Readout agent composes a sourced narrative.

## Cross-cutting
- **Config & secrets:** env vars (`.env.example`), no secrets in code. Settings via Pydantic.
- **Observability:** structured logs, request IDs, agent-run traces (every tool call recorded).
- **Idempotency:** event ingestion is idempotent on `(unit_id, event, dedup_key)`.
- **Caching:** assignment config cached in-process with TTL + invalidation on experiment change.
- **Testing:** stats + assignment have golden-fixture tests; API has contract tests; agents have
  an eval harness with synthetic experiments that have known ground truth.

## Scaling path (don't build now, just don't block it)
- Ingestion: HTTP → Redis Streams / Kafka → warehouse loader.
- Assignment: extract to a tiny stateless service behind a CDN/edge if QPS demands.
- Analytics: DuckDB → MotherDuck / Snowflake / BigQuery / Databricks via the same adapter.
- Multi-region, read replicas for Postgres.

## Non-functional targets (MVP)
- Assignment p99 < 10 ms (in-process, cached).
- Analysis of a 10M-event experiment < 60 s on DuckDB on a laptop.
- Every result reproducible from stored sufficient statistics + method config.
