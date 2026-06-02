# P02 — Core data model (M1)

**Goal:** implement the Postgres metadata schema as SQLModel models + Alembic migrations.

**Read first:** `docs/03-data-model.md` (authoritative), `docs/02-architecture.md` (store
separation). Event-data tables (DuckDB) are NOT in this prompt — they come in P06.

## Deliverables
- SQLModel models in `app/models/` for the **metadata tables** in `docs/03-data-model.md`:
  `organization`, `workspace`, `user`, `membership`, `experiment`, `variant`, `layer`,
  `metric`, `experiment_metric`, `analysis_run`, `metric_result`, `srm_check`, `readout`,
  `agent_run`, `agent_step`, `api_key`, `audit_log`.
- Match field names, types, enums, and relationships from the doc. UUIDv7 primary keys;
  `created_at`/`updated_at` on every table; `org_id` on every tenant-scoped table (even though
  enforcement is M6).
- Enums for `experiment.status`, `metric.type`, `metric.direction`, `experiment_metric.role`,
  `membership.role`, `experiment.decision`, `agent_run.agent_type`, `agent_step.kind`.
- Alembic initialized; one migration creating all tables; `alembic upgrade head` works against
  the compose Postgres.
- A repository/service seam in `app/services/` (thin CRUD helpers) — no API yet (that's P03).
- Tests: models import; a migration round-trip test (upgrade → create one row per table via a
  fixture → query) using a test Postgres (or SQLite-compatible subset where feasible; prefer a
  Postgres test container).

## Acceptance criteria
- `alembic upgrade head` creates every table with the documented columns/constraints.
- Unique constraints: `experiment.key` per workspace, exactly-one `is_control` per experiment
  enforced at the service layer (document if DB-level is impractical).
- `pytest` green; `mypy`/`ruff` clean.
- A short `docs/03-data-model.md` note if you had to deviate (and why).

## Notes
- Keep models free of business logic; put invariants (e.g. variant allocations sum to 100,
  exactly one control) in service-layer validators with tests.
- `jsonb` fields (`allocation`, `targeting`, `payload`, `method`, `props`…) as typed Pydantic
  sub-models serialized to JSON, so the API and agents get type safety.

## Commit
`feat: metadata models + initial migration`. Suggested model: **medium**.
