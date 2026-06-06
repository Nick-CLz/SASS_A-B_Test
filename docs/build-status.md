# Build status — claims vs. reality

Honest map of what `docs/pitch.html` (and the tier table in [`11-sales.md`](./11-sales.md))
sells against what is actually implemented in this repo today. Keep this current — it is the
source of truth the sales materials must not contradict.

**Legend:** ✅ **Live** (built & tested) · 🟡 **Beta** (foundation shipped; needs one more thing) ·
🗺️ **Roadmap** (planned, not built).

## Platform capabilities
| Capability | Status | Notes |
|---|---|---|
| Deterministic assignment + targeting/layers/holdouts | ✅ Live | Pure hash bucketing; cross-language golden fixtures. |
| Python + TypeScript SDKs | ✅ Live | Same bucketing as the server, fixture-pinned. |
| Privacy-first ingestion (PII guard, allow-list) | ✅ Live | PII rejected with a reason before storage; tested. |
| Embedded analytics (DuckDB) | ✅ Live | Sufficient-statistics interface. |
| Statistics: z/Welch, delta-method CIs, CUPED, sequential, Bayesian, SRM, multiple-comparison, power | ✅ Live | Validated vs scipy/statsmodels; A/A-calibrated; power-simulated. |
| Analysis pipeline + REST API | ✅ Live | `/v1/.../analyze`, `/results`, `/power`. |
| Dashboard (list + results + SRM banner) | ✅ Live | Next.js. |
| Multi-tenancy + RBAC + audit log + API keys | ✅ Live | Tenant isolation proven by test. |
| Grounded-AI mechanism ("never invents numbers") | ✅ Live | Tools + ungrounded-number check + persisted traces; tested with a mock model. |
| **AI agents** (Designer / Monitor / Analyst / Readout) | 🟡 Beta | Foundation + grounding done & tested. The 4 concrete agents are **not yet written**, and live runs need `ANTHROPIC_API_KEY`. **This is the headline — not yet end-to-end.** |
| "Runs on **your warehouse**" (BigQuery / Snowflake / Databricks) | 🗺️ Roadmap | Only DuckDB is implemented. Warehouse names exist as enum values; **no connector code.** Designed as an adapter swap. |
| Self-host / VPC deploy | 🟡 Beta | Deployable via Docker/compose + `deploy.md`. "VPC / DPA / security review" are process, not code. |
| **SSO / SAML / SCIM** | 🗺️ Roadmap | Not in the codebase. Auth today = API keys + dev role header. |
| **Billing / usage metering** (AI runs, seats) | 🗺️ Roadmap | No Stripe, no metering. Tier prices are illustrative hypotheses. |
| Additional warehouse connectors | 🗺️ Roadmap | Only DuckDB today. |

## What each gap takes to close
- **AI agents (Beta → Live):** write the 4 agents on the existing runner + grounding; add
  `/v1/.../agents` endpoints. Needs `ANTHROPIC_API_KEY` to run/verify. ~1 build cycle.
- **Warehouse connector (Roadmap → Beta):** implement the `AnalyticsBackend` adapter interface
  against the existing sufficient-statistics queries; add one connector (e.g. BigQuery). Medium.
- **SSO/SCIM (Roadmap):** add an OIDC/SAML provider behind the pluggable auth in `deps.py`. Medium.
- **Billing/metering (Roadmap):** count agent runs / events per workspace, expose usage, integrate
  a billing provider. Medium.

## Rule
The pitch may show **vision**, but anything presented as *available in a tier* must be ✅ Live here,
or be clearly marked Beta/Roadmap. When a gap closes, update this file in the same change.
