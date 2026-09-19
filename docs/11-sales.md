# 11 — Sales & pricing (sell + expand)

Concrete packaging for **Track B** (sellable SaaS) in [`08-go-to-market.md`](./08-go-to-market.md).
Prices here are **illustrative hypotheses to test**, not commitments. The motion is
**land-and-expand**: land on Free/Team, expand through AI-agent usage, seats, and governance.

## One-line pitch
> **The AI-native, privacy-first experimentation platform.** Agents design, monitor, analyze,
> and write up your experiments on top of a statistics engine you can actually trust — on your
> own data warehouse. *5–10× more experiments analyzed per data scientist, with rigor raised,
> not lowered.*

## Who buys & why now
Mid-to-large teams with a real experimentation practice where **a few data scientists gate
everything**. The AI agents remove that bottleneck; the deterministic engine (grounded AI, SRM,
CUPED, sequential, Bayesian) is the trust moat. Privacy-first + warehouse-native means raw data
never leaves their perimeter — a board-level requirement for regulated and privacy-focused buyers.

## Packaging

| | **Free** | **Team** | **Business** | **Enterprise** |
|---|---|---|---|---|
| **Price** *(illustrative)* | $0 forever | $49 / editor seat / mo | $99 / editor seat / mo | Custom |
| Core engine + assignment + SDKs | ✅ | ✅ | ✅ | ✅ |
| Frequentist stats + dashboard | ✅ | ✅ | ✅ | ✅ |
| Advanced stats (CUPED, sequential, Bayesian) | — | ✅ | ✅ | ✅ |
| **AI agents** (design/monitor/analyze/readout) | — | ✅ metered | ✅ higher quota | ✅ custom routing |
| Warehouse connectors | DuckDB | 1 | multiple | unlimited + self-host |
| Workspaces / seats | 1 / 3 | unlimited viewers | unlimited | unlimited |
| Governance: RBAC + audit log | basic | ✅ | ✅ + retention | ✅ + exports |
| SSO / SAML / SCIM | — | — | ✅ SSO | ✅ SAML + SCIM |
| Self-host / VPC, DPA, security review | — | — | — | ✅ |
| Support | community | email | priority + SLA | dedicated CSM |

**Free is the wedge** (adoption + the open-core portfolio story). **Team** unlocks the headline
(AI agents + advanced stats). **Business** adds governance/SSO. **Enterprise** adds
self-host/compliance.

## Expansion levers (how the account grows = net revenue retention)
1. **AI-agent usage** — metered by agent runs / tokens. The primary expansion line; grows
   naturally as teams analyze more experiments. Healthy margin comes from the model-routing +
   prompt-caching design in [`05-ai-agents.md`](./05-ai-agents.md).
2. **Seats** — more editors/analysts as experimentation spreads beyond the core DS team.
3. **Warehouse connectors** — BigQuery / Snowflake / Databricks beyond the first.
4. **Governance & security** — SSO, audit retention, SCIM (Business → Enterprise trigger).
5. **Self-host / VPC + compliance** (DPA, security review) — the Enterprise unlock for regulated buyers.

## The value math (the upsell story)
A senior DS costs ~$200k fully loaded and spends ~40% of their time on analysis/readouts. If
agents handle most of that, you reclaim **~$60–80k of capacity per DS per year** — and ship
faster: time-from-stop-to-readout drops from days to minutes, and SRM catches the bad tests
*before* a wrong decision ships. At $49–99/seat, the platform pays for itself on the first
prevented bad ship or the first DS-week reclaimed.

## Objection handling
- **"Can I trust an LLM with statistics?"** — The LLM never computes a number. The engine
  computes; the agent narrates; every figure is traced to a tool call (grounding). Auditable.
- **"We have a warehouse / data can't move."** — Analytics run warehouse-native; raw data stays
  in your perimeter. Self-host on Enterprise.
- **"We already use flags (LaunchDarkly/Split)."** — Keep them; Mallard is the analysis + brain
  layer, not a flag tool. We complement flagging with rigorous analysis and agentic workflow.
- **"How is this different from Statsig/Eppo?"** — Same warehouse-native rigor, plus **agents
  that do the DS workflow** and a **privacy-first** posture.

## Sales motion
Product-led on Free → in-product upsell when a team hits an agent/advanced-stat gate →
sales-assisted for Business/Enterprise (SSO, self-host, security review). Prove value with the
metrics in [`08-go-to-market.md`](./08-go-to-market.md#metrics-to-prove-value-for-either-track):
experiments/DS/week, hypothesis→launch and stop→readout time, SRM catches, AI cost/experiment.
