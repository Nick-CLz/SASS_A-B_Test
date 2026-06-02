# P09 — Results & analysis API (M2/M3)

**Goal:** wire the analytics adapter + stats engine into an analysis pipeline and expose
results, SRM, power, and diagnostics over the API. This is the seam the dashboard and agents
both consume.

**Read first:** `docs/06-api-and-sdk.md` §Results, `docs/03-data-model.md`
(`analysis_run`/`metric_result`/`srm_check`), `docs/04-statistics-engine.md` (what to compute),
`docs/02-architecture.md` §"Analyze" flow. Builds on P06 + P07 (P08 optional but supported).

## Deliverables
- `app/services/analysis.py` — orchestrates one analysis run:
  1. pull sufficient statistics from the `AnalyticsBackend` (P06),
  2. run **SRM first** (P07 diagnostics),
  3. compute per-metric × per-variant results via the stats engine (frequentist always;
     CUPED/sequential/Bayesian/segments if configured — P08),
  4. apply multiple-comparison correction across the metric family,
  5. persist an `analysis_run` + `metric_result` rows + `srm_check`.
- Endpoints from `docs/06-api-and-sdk.md`:
  - `POST /v1/experiments/{key}/analyze` (method config in body: which methods, α, correction,
    CUPED covariate, segments),
  - `GET /v1/experiments/{key}/results` (latest run) and `/results/{run}` (specific),
  - `GET /v1/experiments/{key}/power`.
- The results payload surfaces the **SRM flag prominently** and includes `method_detail` so the
  UI/agent can explain each number.
- Tests: end-to-end on synthetic data (P06 generator) — known effect recovered within CI;
  injected SRM flagged and surfaced; results persisted and re-readable; correction applied.

## Acceptance criteria
- `analyze` produces persisted, re-readable results matching the engine's output.
- SRM is computed first and clearly flagged in the response; when flagged, results are marked
  untrustworthy.
- Power endpoint returns sample-size/MDE/runtime.
- Reproducibility: same stored sufficient statistics + method config → identical results.
- `pytest` green; `ruff`/`mypy` clean.

## Commit
`feat: analysis pipeline + results/power API`. Suggested model: **medium**.
