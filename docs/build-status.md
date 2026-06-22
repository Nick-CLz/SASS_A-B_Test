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
| Warehouse-native analytics (`AnalyticsBackend` + `SqlStore`) | 🟡 Beta | DuckDB live; `SqlStore` runs the same sufficient-statistics queries on any SQLAlchemy SQL warehouse — parity-tested vs DuckDB. Cloud dialects (BigQuery/Snowflake/Databricks) need their driver + creds (untested). |
| Self-host / VPC deploy | 🟡 Beta | Deployable via Docker/compose + `deploy.md`. "VPC / DPA / security review" are process, not code. |
| SSO bearer tokens (OIDC-style HS256 JWT) | 🟡 Beta | `Authorization: Bearer` JWTs verified (signature + exp), claims → role; tested. RS256/JWKS from an IdP, SAML, and SCIM remain roadmap. |
| **Usage metering** (AI agent runs + tokens, analyses; `GET /v1/usage`) | ✅ Live | Per-org aggregation from the trace tables; admin-gated; tested. |
| Invoice computation (rate card × usage; `GET /v1/billing/invoice`) | ✅ Live | Deterministic pricing of metered usage into line items + total; tested. |
| Charging via a provider (Stripe) | 🗺️ Roadmap | Invoice math is done; the provider charge + webhook is not. Prices illustrative. |
| Cloud warehouse dialects (BigQuery/Snowflake/Databricks) | 🗺️ Roadmap | `SqlStore` covers standard SQL; cloud-specific drivers + warehouse-native idempotent load aren't wired/tested. |

## What each gap takes to close
- **AI agents (Beta → Live):** write the 4 agents on the existing runner + grounding; add
  `/v1/.../agents` endpoints. Needs `ANTHROPIC_API_KEY` to run/verify. ~1 build cycle.
- **Cloud warehouse connector (Roadmap):** `SqlStore` (SQLAlchemy) is live for standard SQL and
  parity-tested; add the dialect driver + warehouse-native idempotent load for BigQuery/Snowflake. Medium.
- **SSO (Roadmap, on the bearer path):** HS256 bearer JWTs are live behind the pluggable auth;
  add RS256/JWKS from the IdP, SAML, and SCIM provisioning. Medium.
- **Charging (Roadmap):** metering + invoice computation are live (`/v1/usage`,
  `/v1/billing/invoice`); add a provider (Stripe) charge + webhook on top. Medium.

## Rule
The pitch may show **vision**, but anything presented as *available in a tier* must be ✅ Live here,
or be clearly marked Beta/Roadmap. When a gap closes, update this file in the same change.
