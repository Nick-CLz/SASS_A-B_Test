# 06 — API & SDK

REST under `/v1`, JSON, generated OpenAPI (FastAPI). Auth via API key (server) or session
(dashboard); scopes: `assign`, `track`, `admin`. All endpoints are tenant-scoped.

## Endpoint map

### Experiments & config (dashboard / admin)
```
POST   /v1/experiments                     create (draft)
GET    /v1/experiments                      list (filter by status, workspace)
GET    /v1/experiments/{key}                read (with variants, metrics)
PATCH  /v1/experiments/{key}                update (only in draft/review)
POST   /v1/experiments/{key}/transition     status change (review/run/pause/conclude/archive)
POST   /v1/experiments/{key}/variants       add variant
POST   /v1/experiments/{key}/metrics        attach metric (role: primary/secondary/guardrail)
GET    /v1/metrics  | POST /v1/metrics       reusable metric definitions
GET    /v1/layers   | POST /v1/layers        mutual-exclusion groups & holdouts
```

### Assignment (hot path, SDK)
```
POST   /v1/assign
  body: { unit_id, experiment_key?, attributes? }      # one experiment, or…
  body: { unit_id, attributes? }                        # all eligible experiments
  → { assignments: [{ experiment_key, variant_key, payload, in_experiment }] }
```
Deterministic, cached config, no DB on the hot path. The SDK auto-logs an **exposure** unless
told to defer (for "assign now, expose on actual use" patterns).

### Ingestion (hot path, SDK)
```
POST   /v1/events            # batched
  body: { events: [{ unit_id, name, ts, value?, props? }], exposures: [{...}] }
  → { accepted, rejected: [{ index, reason }] }         # PII-guard / schema rejections explained
```
Idempotent on `event_id`/dedup key. Rejects (not silently drops) anything failing the PII guard
or the workspace event allow-list, with a reason.

### Results & analysis
```
POST   /v1/experiments/{key}/analyze        # run/refresh analysis (method config in body)
GET    /v1/experiments/{key}/results        # latest metric_results + SRM + diagnostics
GET    /v1/experiments/{key}/results/{run}  # a specific analysis_run
GET    /v1/experiments/{key}/power          # sample-size / MDE / runtime
```

### AI agents
```
POST   /v1/experiments/{key}/agents/designer   { hypothesis, context } → draft config + rationale
POST   /v1/experiments/{key}/agents/monitor    → health status + alerts
POST   /v1/experiments/{key}/agents/analyst    → interpreted results (sourced)
POST   /v1/experiments/{key}/agents/readout    → readout (markdown + decision + sources)
GET    /v1/experiments/{key}/agents/runs       → agent_run + agent_step traces (audit)
```

## SDK design (Python + TypeScript)
Same surface in both languages.

```python
mallard = Mallard(api_key=..., base_url=...)

# assignment (exposure auto-logged)
variant = mallard.get_variant("new_checkout", unit_id=user_id, attributes={"country": "US"})
if variant.key == "treatment":
    ...

# tracking (batched + flushed)
mallard.track(unit_id=user_id, name="purchase", value=42.00, props={"sku_count": 3})
```
- **Local vs. remote assignment:** SDK can fetch experiment configs and bucket *locally* (sub-ms,
  no network on the hot path) or call `/v1/assign`. Bucketing logic is identical to the server's
  and shares golden-fixture tests so client and server never disagree.
- **Privacy in the SDK:** `unit_id` must be a pseudonymous ID; `attributes`/`props` are typed and
  validated against the workspace allow-list; the SDK refuses obvious PII fields client-side.
- **Exposure semantics:** `get_variant` logs an exposure by default; `peek_variant` does not (for
  "assign but only expose on real use" / triggered analysis).
- **Resilience:** non-blocking, batched event flush; safe defaults (return control + log nothing
  if the service is unreachable) so experiments never break the host app.

## Versioning & errors
- `/v1` is stable; additive changes only within a major version.
- Errors are typed: `{ error: { code, message, details? } }`; 4xx for client, 5xx for server.
- Rate limits per API key; `429` with `Retry-After`.

## OpenAPI & codegen
FastAPI emits the OpenAPI spec; the TS SDK types are generated from it (or hand-written and
contract-tested against it) so the dashboard and SDK never drift from the server.
