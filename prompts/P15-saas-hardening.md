# P15 — Multi-tenancy, auth, RBAC, audit (M6)

**Goal:** make it a real SaaS: isolate tenants, authenticate users + API keys, enforce roles,
and record an immutable audit trail. Because `org_id` has been on every tenant-scoped table
since M1, this is mostly enforcement + auth, not a migration.

**Read first:** `docs/03-data-model.md` (org/workspace/user/membership/api_key/audit_log),
`docs/06-api-and-sdk.md` (scopes), `docs/10-decisions.md` D6, `docs/01-product-vision.md`
(privacy/auditability).

## Deliverables
- **Auth:** session auth for the dashboard and **API-key** auth (scopes: `assign`/`track`/
  `admin`) for SDK/server calls. Pluggable provider (`AUTH_PROVIDER=stub|jwt|clerk`) so the MVP
  stub becomes real without rewrites. Replace the P03 stubbed auth dependency.
- **Tenant isolation:** every query filtered by `org_id`/`workspace_id` from the authenticated
  principal; add a test that **org A cannot read or mutate org B's** experiments, results,
  events, or agent runs.
- **RBAC:** roles `owner/admin/editor/analyst/viewer` enforced on each endpoint (e.g. only
  editor+ can transition an experiment; viewers read-only). Centralized permission checks +
  tests.
- **Audit log:** write immutable `audit_log` entries for sensitive actions (experiment
  transitions, metric changes, agent-recommended pauses, ship decisions, key creation) with
  before/after.
- **Rate limiting** per API key (`429` + `Retry-After`).

## Acceptance criteria
- Cross-tenant access is impossible (explicit negative tests across every tenant-scoped
  resource, including analytics/event data and agent traces).
- RBAC enforced with tests for each role boundary.
- Sensitive actions produce audit entries; audit is append-only.
- API keys authenticate SDK calls with correct scopes; rate limiting works.
- `pytest` green; `ruff`/`mypy` clean.

## Notes
- Privacy carries over: still no PII in events; auth identifiers (emails) live only in the
  `user` table, never in the event stream/analytics.

## If you must split this
auth+isolation first (the security core), then RBAC, then audit + rate limiting.

## Commit
`feat: auth + tenant isolation`, `feat: rbac`, `feat: audit log + rate limiting`. Model: **medium**.
