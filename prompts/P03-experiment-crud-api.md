# P03 — Experiment CRUD & lifecycle API (M1)

**Goal:** the REST surface to create and manage experiments, variants, metrics, and layers,
including lifecycle transitions.

**Read first:** `docs/06-api-and-sdk.md` (endpoint map), `docs/03-data-model.md`,
`docs/01-product-vision.md` (lifecycle states). Builds on P02.

## Deliverables
- FastAPI routers under `app/api/v1/` implementing (from `docs/06-api-and-sdk.md`):
  - experiments: create/list/get/patch, `POST .../transition` (status machine),
  - variants: add/update (allocations must sum to 100; exactly one control),
  - metrics: reusable definitions CRUD,
  - `experiment_metric`: attach metric with a role + MDE + `is_oec`,
  - layers: create/list (mutual exclusion + holdout partitions).
- Pydantic request/response schemas (separate from DB models).
- A **status state machine** enforcing valid transitions
  (`draft→review→running→paused→concluded→archived`, with allowed back-edges) and blocking edits
  to config once `running`.
- Service-layer validation: allocation sums, single control, targeting schema, key uniqueness.
- Generated OpenAPI; verify it renders at `/docs`.
- Tests: happy-path CRUD, invalid transitions rejected, allocation/control invariants enforced,
  can't edit a running experiment's variants.

## Acceptance criteria
- All endpoints in `docs/06-api-and-sdk.md` §"Experiments & config" exist and are tested.
- Invalid lifecycle transitions return a typed 4xx with a clear message.
- Invariants enforced with tests (allocations sum to 100; one control; unique key per
  workspace).
- `pytest` green; OpenAPI at `/docs`; `ruff`/`mypy` clean.

## Notes
- Tenant scoping: accept `workspace_id`/`org_id` context (from a stubbed auth dependency for
  now — real auth is P15) and filter by it everywhere, so M6 is a swap, not a rewrite.
- Keep handlers thin; logic in `app/services/`.

## Commit
`feat: experiment/variant/metric/layer API + lifecycle`. Suggested model: **medium**.
