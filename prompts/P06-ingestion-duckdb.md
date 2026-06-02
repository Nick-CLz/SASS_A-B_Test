# P06 — Event ingestion + DuckDB analytics (M2)

**Goal:** accept exposure + metric events (privacy-guarded), store them in DuckDB, and expose
an analytics adapter that returns the **sufficient statistics** the stats engine needs.

**Read first:** `docs/02-architecture.md` §Ingestion/§Analytics, `docs/03-data-model.md`
§"Event data", `docs/01-product-vision.md` §Privacy, `docs/06-api-and-sdk.md` §Ingestion.

## Deliverables
- `POST /v1/events` (batched): validate each event against the workspace **event allow-list**
  (typed property schema), run the **PII guard** (reject/redact emails, phones, raw IPs,
  free-text that looks like PII), idempotent on `event_id`. Return per-item accept/reject with
  reasons.
- `app/ingestion/` writes `exposures` and `events` to DuckDB (schema per `docs/03-data-model.md`).
  Design the writer behind an interface so a queue/warehouse loader can replace it later.
- `app/analytics/` — the **`AnalyticsBackend` adapter** with a DuckDB implementation. It returns
  **sufficient statistics only** (never raw rows):
  - per-variant: `n`, sum, sum-of-squares (for means/variance), success/total (for proportions),
  - for ratio metrics: per-variant numerator/denominator sums + cross terms,
  - for CUPED: `Cov(Y, X)`, `Var(X)`, means (X = pre-period metric),
  - per-day series and per-segment slices (for novelty + segment analysis),
  - arm exposure counts (for SRM).
  One templated group-by per metric; keep SQL warehouse-portable (note where dialects differ).
- A synthetic data generator (fixture/util) producing exposures + events with a *known* effect,
  optional injected SRM, and a pre-period covariate — reused by P07/P08 tests and the demo.
- Tests: allow-list validation, PII guard rejects PII (asserts none reaches DuckDB),
  idempotency, and that the adapter's sufficient stats match hand-computed values on a small
  fixture.

## Acceptance criteria
- Events violating the allow-list or PII guard are **rejected with reasons** (not silently
  dropped); a test asserts no PII column/value lands in DuckDB.
- The adapter returns correct sufficient statistics on a known fixture (exact match).
- Re-sending the same `event_id` doesn't double-count.
- `pytest` green; `ruff`/`mypy` clean.

## Notes
- The stats engine must never receive raw rows — only sufficient statistics. This keeps it pure
  and warehouse-native (D2/D5 in `docs/10-decisions.md`).
- Make the synthetic generator seedable and documented; it's the backbone of stats + agent
  tests and the demo.

## Commit
`feat: event ingestion + duckdb analytics adapter`. Suggested model: **medium**.
