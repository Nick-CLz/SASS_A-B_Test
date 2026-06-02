# P05 — SDKs: Python + TypeScript (M1)

**Goal:** client libraries for assignment + tracking, with **local bucketing that matches the
server byte-for-byte**.

**Read first:** `docs/06-api-and-sdk.md` §SDK, `docs/04-statistics-engine.md` §Assignment, and
the golden fixtures from P04. Builds on P04 (and P06 for tracking, but the track API contract is
in the API doc, so you can build against it).

## Deliverables
`sdks/python/` and `sdks/typescript/`, each with:
- `getVariant(experimentKey, unitId, attributes)` — local bucketing using the **same hash
  construction** as P04; logs an exposure by default; `peekVariant` does not.
- `track(unitId, name, value?, props?)` — batched, non-blocking flush to `/v1/events`.
- Config fetch + in-memory cache of experiment configs (with refresh), enabling offline-ish
  local assignment; fall back to `/v1/assign` if configs aren't loaded.
- **Privacy guards:** reject obvious PII fields in `attributes`/`props` client-side; require a
  pseudonymous `unitId`.
- **Resilience:** if the service is unreachable, `getVariant` returns control and logs nothing;
  `track` buffers and retries — never throw into the host app.
- Tests in both languages that **load the P04 golden fixtures** and assert identical bucketing.

## Acceptance criteria
- Both SDKs reproduce the P04 golden `(salt, unit_id) → variant` fixtures exactly (parity test
  green in both languages).
- `track` batches and flushes; failures don't throw.
- PII guard rejects e.g. a field named `email`/`phone` or value matching an email regex (with
  tests).
- Each SDK has a README with a 5-line quickstart matching `docs/06-api-and-sdk.md`.

## Notes
- Keep the hashing code tiny and shared-in-spirit across languages; the cross-language fixture
  file is the contract.
- The TS SDK should be usable both server-side (Node) and as a thin client.

## If you must split this
Python SDK first (parity test green), then TS SDK reusing the same fixtures.

## Commit
`feat: python sdk`, `feat: typescript sdk`. Suggested model: **medium**.
