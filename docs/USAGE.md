# Using Mallard — a manual

How to run the platform and drive a real experiment end-to-end. Two paths:

- **[A. The demo](#a-the-demo-zero-setup)** — see the whole statistics story in one command (no setup).
- **[B. The live API + dashboard](#b-the-live-api--dashboard)** — create and analyze your own experiment.

If you only do one thing, run `make demo`.

---

## Concepts (60 seconds)

| Term | What it is |
|---|---|
| **Organization → Workspace** | Tenant boundary. Every request targets one workspace via the `X-Workspace-Id` header. |
| **Experiment** | A test with a lifecycle: `draft → review → running → … `. Has **variants**. |
| **Variant** | One arm (e.g. `control`, `treatment`) with an `allocation_pct`. Exactly one is the control. |
| **Metric** | What you measure (e.g. purchase conversion). The **OEC** is the primary decision metric. |
| **Assignment** | Which variant a unit (user) gets — a pure, deterministic hash. Same unit → same variant, always. |
| **Exposure / Event** | An exposure = "unit saw the experiment"; an event = something they did (e.g. `purchase`). |
| **Analysis** | The stats run: per-variant rates, lift + confidence interval, p-value, Bayesian P(better), and an **SRM** data-quality check. |
| **Roles** | `viewer < analyst < editor < admin < owner`. Reads are open; writes need editor; analyze needs analyst; admin endpoints need admin. |

**Privacy:** units are pseudonymous IDs. The ingestion guard **rejects PII** (emails, phones, IPs) with a reason — it never reaches storage.

---

## A. The demo (zero setup)

```bash
make demo        # or: cd backend && uv run python -m scripts.demo
```
Runs the full pipeline on in-memory stores. You'll see:
- a **winning** experiment — `+33%` relative lift, 95% CI, `p ≈ 5e-14`, **SIGNIFICANT**, plus Bayesian P(better);
- a **broken** experiment — caught by **SRM** (χ² ≈ 1143) → *"results NOT trustworthy"*;
- a **power** calculation (sample size for a target effect).

Every number is computed by the deterministic stats engine — none is invented.

---

## B. The live API + dashboard

### 1. Start the API + seed a workspace
Use a file-backed SQLite DB so the seed and the server share data (no Postgres needed):

```bash
cd backend
export DATABASE_URL=sqlite:///./mallard.db

uv run python -m scripts.seed            # prints: export WS=…  export KEY=…
uv run uvicorn app.main:app --reload     # API on http://localhost:8000  (docs at /docs)
```
Copy the two `export` lines the seed prints into your shell:
```bash
export WS=<workspace-id-from-seed>
export KEY=<api-key-from-seed>           # admin key; sets your role to admin
```
> Auth: every request sends `X-Workspace-Id: $WS`. For writes, also send the admin key
> `X-Api-Key: $KEY`. (For quick local tinkering you can instead send `X-Role: editor` —
> the dev header — but the API key is the real path.)

### 2. Create an experiment (editor+)
```bash
curl -s -X POST localhost:8000/v1/experiments \
  -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"key":"checkout_v2","name":"New checkout",
       "hypothesis":"A cleaner checkout lifts purchase conversion.",
       "variants":[{"key":"control","is_control":true,"allocation_pct":50},
                   {"key":"treatment","allocation_pct":50}]}'
```

### 3. Attach the primary metric
The seed already created a `conv` metric (purchase conversion). Attach it as the OEC — use the
`conv` id the seed printed (or create your own metric via `POST /v1/metrics`):
```bash
curl -s -X POST localhost:8000/v1/experiments/checkout_v2/metrics \
  -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"metric_id":"<CONV_METRIC_ID>","role":"primary","is_oec":true,"min_detectable_effect":0.02}'
```

### 4. Launch it
```bash
curl -s -X POST localhost:8000/v1/experiments/checkout_v2/transition \
  -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY" -H 'Content-Type: application/json' -d '{"status":"review"}'
curl -s -X POST localhost:8000/v1/experiments/checkout_v2/transition \
  -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY" -H 'Content-Type: application/json' -d '{"status":"running"}'
```

### 5. Assign a unit
```bash
curl -s -X POST localhost:8000/v1/assign \
  -H "X-Workspace-Id: $WS" -H 'Content-Type: application/json' \
  -d '{"unit_id":"user-123","experiment_key":"checkout_v2"}'
# → {"assignments":[{"experiment_key":"checkout_v2","eligible":true,
#                    "in_experiment":true,"variant_key":"treatment","reason":"assigned"}]}
```
`/assign` is deterministic (same `unit_id` → same variant) **and it records the exposure for you**.

### 6. Send a conversion event
```bash
curl -s -X POST localhost:8000/v1/events \
  -H "X-Workspace-Id: $WS" -H 'Content-Type: application/json' \
  -d '{"events":[{"unit_id":"user-123","name":"purchase","value":42.0}]}'
# → {"accepted":1,"rejected":[]}        (PII or non-allow-listed events come back in "rejected")
```

#### Generate enough traffic to be significant (optional)
One user won't move a p-value. This loop assigns ~1500 units and converts treatment a bit more
often (it's slow — for the full statistical story just run `make demo`):
```bash
for i in $(seq 1 1500); do
  v=$(curl -s -X POST localhost:8000/v1/assign -H "X-Workspace-Id: $WS" \
        -H 'Content-Type: application/json' \
        -d "{\"unit_id\":\"u$i\",\"experiment_key\":\"checkout_v2\"}" \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['assignments'][0]['variant_key'])")
  t=$(( RANDOM % 100 ))
  if { [ "$v" = control ] && [ $t -lt 10 ]; } || { [ "$v" = treatment ] && [ $t -lt 14 ]; }; then
    curl -s -X POST localhost:8000/v1/events -H "X-Workspace-Id: $WS" \
      -H 'Content-Type: application/json' \
      -d "{\"events\":[{\"unit_id\":\"u$i\",\"name\":\"purchase\"}]}" > /dev/null
  fi
done
```

### 7. Analyze + read results
```bash
curl -s -X POST localhost:8000/v1/experiments/checkout_v2/analyze \
  -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"alpha":0.05,"correction":"benjamini_hochberg","bayesian":true}'
```
The response (and `GET /v1/experiments/checkout_v2/results`) includes:
- `srm` — the sample-ratio check (**look here first**; if `is_mismatch` is true, don't trust the rest);
- `results[]` — per variant: `estimate`, `abs_effect`, `rel_effect`, `ci_lower/ci_upper`,
  `p_value`, `is_significant`, and (for proportions) `prob_to_beat_control` + `expected_loss`.

### 8. Plan a future test (power)
```bash
curl -s "localhost:8000/v1/experiments/checkout_v2/power?baseline=0.10&mde=0.02&daily_traffic=2000" \
  -H "X-Workspace-Id: $WS"
# → sample_size_per_arm, total_sample_size, runtime_days
```

### The dashboard
```bash
cd frontend && pnpm dev          # http://localhost:3000
```
Set `NEXT_PUBLIC_API_BASE_URL` (API URL) and `NEXT_PUBLIC_WORKSPACE_ID=$WS`. You get the
experiment list and a results view that leads with the confidence interval and shows a loud
banner when SRM fails.

---

## Admin: API keys, roles, audit
```bash
# create another key (admin)
curl -s -X POST localhost:8000/v1/api-keys -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY" \
  -H 'Content-Type: application/json' -d '{"name":"sdk","scopes":["assign","track"]}'
# list keys (secrets are never returned again)
curl -s localhost:8000/v1/api-keys -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY"
# audit trail of sensitive actions (admin)
curl -s localhost:8000/v1/audit -H "X-Workspace-Id: $WS" -H "X-Api-Key: $KEY"
```
A key's scopes set its role: `admin` scope → admin; otherwise editor (can assign/track/create).
A `viewer`/`analyst` will get **403** on writes — that's the RBAC working.

---

## SDKs (in app code instead of curl)
`sdks/python` and `sdks/typescript` wrap `/assign` + `/events` with the *same* deterministic
bucketing as the server (pinned by shared golden fixtures), so client-side assignment matches
the backend exactly. See each SDK's README.

## Troubleshooting
- **404 "workspace not found"** — `X-Workspace-Id` is wrong or you seeded a different DB. Re-run
  `scripts.seed` with the same `DATABASE_URL` the server uses.
- **403 forbidden** — your role is too low; send the admin `X-Api-Key` (or `X-Role: editor`).
- **event in `rejected`** — it tripped the PII guard or a workspace allow-list. The `reason` says which.
- **results look flat / not significant** — you need volume; run the traffic loop above or `make demo`.

## What needs a key
The AI agents (design/monitor/analyze/write-up) call this same engine through audited tools.
The foundation + grounding are built and tested; running the agents live needs `ANTHROPIC_API_KEY`
set in the environment. Full plan: `docs/05-ai-agents.md`.
