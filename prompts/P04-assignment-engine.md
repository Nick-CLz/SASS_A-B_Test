# P04 — Assignment engine (M1) — correctness-critical

**Goal:** deterministic bucketing with targeting, traffic allocation, variant split, layers
(mutual exclusion), holdouts, and orthogonality across experiments. **A bug here invalidates
every result** — use a strong model and over-test.

**Read first:** `docs/04-statistics-engine.md` §Assignment (authoritative algorithm),
`docs/03-data-model.md` (experiment/variant/layer fields), `docs/06-api-and-sdk.md` (`/v1/assign`).

## Deliverables
- Pure module `app/assignment/` with no I/O:
  - `bucket(unit_id, salt) -> float in [0,1)` using a stable 64-bit hash (SHA-256 → 64 bits;
    document the exact construction so the SDKs can match it byte-for-byte).
  - `evaluate_targeting(attributes, targeting) -> bool`.
  - `assign(unit_id, experiment, attributes) -> Assignment(variant_key | not_in_experiment | not_eligible)`
    applying: targeting → traffic allocation → variant split.
  - Layer logic: experiments in the same layer are mutually exclusive (shared partitioned hash
    space); different layers are independent. Holdout = reserved partition, no treatment.
- `POST /v1/assign` (single + all-eligible forms from the API doc), reading cached experiment
  config (in-process cache with TTL + invalidation on experiment change). No DB on the hot path.
- Exposure logging hook (the endpoint records an exposure unless `peek`/defer is set) — write
  via the ingestion seam (full ingestion is P06; here, stub or buffer if P06 isn't done, behind
  an interface).

## Acceptance criteria (tests are the point here)
- **Determinism:** same `(unit_id, salt)` always → same variant.
- **Uniformity:** `bucket()` over many ids passes a KS test for uniform[0,1).
- **Split correctness:** at N=1e6, observed variant shares match `allocation_pct` within
  tolerance.
- **Traffic allocation:** only the configured % enters the experiment.
- **Orthogonality:** two experiments with different salts have ~independent assignment
  (cross-tab ≈ product of marginals).
- **Mutual exclusion:** within one layer, no unit is in two experiments; across layers,
  independent.
- **Targeting:** ineligible units are excluded and not counted.
- **Holdout:** holdout units never receive treatment.
- `/v1/assign` p99 < 10 ms locally with warm cache (rough check is fine).
- Provide **golden fixtures** (input → expected variant) that P05 SDKs reuse to prove
  client/server parity.

## Notes
- Document the hash construction precisely (encoding, delimiter, bit extraction) — the SDKs
  must reproduce it exactly. Add a cross-language fixture file (JSON) of `(salt, unit_id) →
  bucket` values.
- Keep `assign()` pure and side-effect-free; the endpoint handles caching + exposure logging.

## Commit
`feat: deterministic assignment engine + /v1/assign`. Suggested model: **large**.
