# 03 — Data model

Two stores (see [`02-architecture.md`](./02-architecture.md)):
- **Postgres** — metadata + computed results (this doc's tables).
- **Analytics engine (DuckDB/warehouse)** — append-only event data (the `events` section).

IDs are UUIDv7 (sortable). All tables have `created_at`, `updated_at`. Tenant-scoped tables
carry `org_id` (multi-tenancy lands in M6 but the column exists from the start so we don't
migrate the world later).

## Entity overview
```
Organization ─┬─< Workspace ─┬─< Experiment ─┬─< Variant
              │              │               ├─< ExperimentMetric >─ Metric
              │              │               ├─< AnalysisRun ─┬─< MetricResult
              │              │               │               └─< SrmCheck
              │              │               ├─< Readout
              │              │               └─< AgentRun ─< AgentStep
              │              ├─< Layer
              │              └─< Metric (shared, workspace-level)
              ├─< Membership >─ User
              ├─< ApiKey
              └─< AuditLog
```

## Metadata tables (Postgres)

### organization
Top tenant. `id`, `name`, `slug`, `plan` (free/pro/enterprise), `settings` (jsonb:
privacy policy, PII rules, default α/power).

### workspace
A project/product area inside an org. `id`, `org_id`, `name`, `slug`,
`default_randomization_unit` (e.g. `user_id`), `analytics_backend` (duckdb/bigquery/…),
`event_schema` (jsonb allow-list of event names + typed properties — the privacy allow-list).

### user / membership
`user`: `id`, `email` (auth only; never in event stream), `name`, `is_active`.
`membership`: `user_id`, `org_id`, `role` (owner/admin/editor/analyst/viewer). RBAC in M6.

### experiment
The core entity.
| field | type | notes |
|---|---|---|
| id | uuid | |
| workspace_id | uuid | |
| key | text | URL-safe, unique per workspace; used as the hashing salt seed |
| name, description | text | |
| hypothesis | text | the product hypothesis (Designer agent reads/writes this) |
| status | enum | `draft`→`review`→`running`→`paused`→`concluded`→`archived` |
| layer_id | uuid? | null = default (orthogonal) layer |
| randomization_unit | text | `user_id` \| `session_id` \| `device_id` \| `account_id` |
| allocation | jsonb | total traffic % into the experiment, ramp schedule |
| targeting | jsonb | eligibility rules (country, platform, %, custom attrs) |
| salt | text | per-experiment salt for independent bucketing (defaults from `key`) |
| seed | text | bucketing seed; rotating it reshuffles assignment (rarely used) |
| start_at, end_at | timestamptz? | |
| owner_id | uuid | |
| decision | enum? | `ship` \| `no_ship` \| `iterate` \| `inconclusive` (set at conclusion) |

### variant
| field | type | notes |
|---|---|---|
| id | uuid | |
| experiment_id | uuid | |
| key | text | e.g. `control`, `treatment`, `treatment_b` |
| name | text | |
| is_control | bool | exactly one true per experiment |
| allocation_pct | numeric | split *within* the experiment's traffic; variants sum to 100 |
| payload | jsonb | the config the SDK returns for this variant (flag values, params) |

### layer
Mutual-exclusion group. Experiments in the **same layer** never co-assign the same unit
(they share a partitioned hash space); experiments in **different layers** overlap
independently (orthogonal). `id`, `workspace_id`, `name`, `traffic_partitions` (jsonb).
Also models **holdouts** (a reserved partition that never receives treatment). See assignment
math in [`04-statistics-engine.md`](./04-statistics-engine.md#assignment).

### metric
Reusable metric definition (workspace-level so it's shared across experiments).
| field | type | notes |
|---|---|---|
| id | uuid | |
| workspace_id | uuid | |
| key, name | text | |
| type | enum | `proportion` \| `mean` \| `ratio` \| `count` |
| numerator | jsonb | event filter + aggregation (e.g. count of `purchase`) |
| denominator | jsonb | for ratio metrics (e.g. count of `session`); else the unit |
| direction | enum | `increase_good` \| `decrease_good` |
| unit | text | analysis unit (often = randomization unit; if not → delta method) |
| winsorize_pct | numeric? | optional outlier capping for heavy-tailed metrics |

### experiment_metric
Join row giving a metric a **role** in an experiment.
`experiment_id`, `metric_id`, `role` (`primary`/`secondary`/`guardrail`),
`min_detectable_effect` (for power), `is_oec` (the one decision metric).

### analysis_run
One computation of results. `id`, `experiment_id`, `computed_at`, `method` (jsonb: frequentist/
bayesian/sequential, α, correction, CUPED on/off, covariates), `window_start/end`,
`trigger` (`scheduled`/`manual`/`agent`), `status`.

### metric_result
The numbers (one row per metric × variant × analysis_run).
| field | type | notes |
|---|---|---|
| analysis_run_id, metric_id, variant_id | uuid | |
| n | bigint | exposed/triggered units (or denominator count) |
| estimate | numeric | mean / proportion / ratio |
| abs_effect, rel_effect | numeric | vs. control (lift) |
| ci_lower, ci_upper | numeric | interval for the effect |
| p_value | numeric? | frequentist/sequential |
| prob_to_beat_control | numeric? | Bayesian posterior P(better) |
| expected_loss | numeric? | Bayesian risk |
| variance, std_error | numeric | |
| is_significant | bool | per method + correction |
| method_detail | jsonb | exact test used, df, correction, CUPED θ, etc. |

### srm_check
Sample-Ratio-Mismatch result per analysis run. `analysis_run_id`, `chi_square`, `p_value`,
`observed` (jsonb counts), `expected` (jsonb), `is_mismatch` (bool, p < threshold).
**If `is_mismatch`, results are flagged untrustworthy in the UI and by the Analyst agent.**

### readout
Agent- or human-authored summary. `id`, `experiment_id`, `analysis_run_id`, `author`
(`agent`/`user_id`), `decision_recommendation` (enum), `confidence`, `body_markdown`,
`sources` (jsonb: the tool calls / result rows it cites). Immutable once published; new
versions are new rows.

### agent_run / agent_step
Full trace for auditability. `agent_run`: `id`, `experiment_id`, `agent_type`
(`designer`/`monitor`/`analyst`/`readout`), `model`, `status`, `cost_tokens`, `latency_ms`.
`agent_step`: `agent_run_id`, `seq`, `kind` (`message`/`tool_call`/`tool_result`),
`tool_name`, `input` (jsonb), `output` (jsonb). This is how we prove **no number was invented**.

### api_key
`id`, `org_id`, `name`, `hashed_key`, `scopes` (assign/track/admin), `last_used_at`.

### audit_log
Immutable. `id`, `org_id`, `actor` (user/agent/system), `action`, `target_type`, `target_id`,
`before`/`after` (jsonb), `created_at`.

## Event data (analytics engine: DuckDB / warehouse)
Append-only, columnar, **no PII**. Two logical tables (Parquet or warehouse tables):

### exposures
When a unit was actually exposed to a variant (fired by the SDK at `getVariant`).
| column | type | notes |
|---|---|---|
| exposure_id | uuid | dedup key |
| experiment_key | text | |
| variant_key | text | |
| unit_id | text | **pseudonymous**; never an email/name |
| ts | timestamp | |
| attrs | json/struct | allow-listed, typed (country, platform…) — no PII |

### events
Metric-generating events.
| column | type | notes |
|---|---|---|
| event_id | uuid | idempotency/dedup |
| unit_id | text | pseudonymous |
| name | text | must be in the workspace event allow-list |
| ts | timestamp | |
| value | double? | for revenue/duration metrics |
| props | json/struct | typed, allow-listed |

**Pre-experiment covariates** for CUPED come from the same `events` table restricted to the
pre-period (no separate table needed). The analytics adapter computes the
`Cov(Y, X)`/`Var(X)` sufficient statistics directly.

## Why this shape
- **Sufficient statistics, not raw rows, cross the boundary.** The stats engine receives
  counts/sums/sums-of-squares/covariances, so analysis is one group-by per metric — cheap and
  warehouse-portable, and the engine stays pure/testable.
- **`org_id` everywhere from day one** so multi-tenancy (M6) is an auth/filter change, not a
  migration nightmare.
- **Full agent traces** (`agent_run`/`agent_step`) make the AI auditable — essential for the
  "grounded, never invents numbers" guarantee and for enterprise trust.
- **No PII in the event store** is enforced structurally (typed allow-list + ingestion guard),
  not by policy alone.
