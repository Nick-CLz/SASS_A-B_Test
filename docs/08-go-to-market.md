# 08 — Go-to-market (the two audiences)

This project serves two goals with one codebase. This doc keeps them honest and separate.

## Track A — Portfolio / interview piece (e.g. DuckDuckGo)
**Goal:** demonstrate senior-data-scientist-level rigor and strong engineering to a
privacy-focused employer.

**What resonates with a privacy-first company:**
- **Privacy-first by construction** (pseudonymous units, no PII in the pipeline, self-host /
  warehouse-native so raw data never leaves the customer). This is the through-line — lead
  with it.
- **Statistical rigor** that a DS interviewer will probe: delta method for ratio metrics,
  CUPED, sequential/always-valid inference, SRM, calibrated A/A tests. The
  [`04-statistics-engine.md`](./04-statistics-engine.md) doc is basically interview gold.
- **Grounded AI** — a credible answer to "how do you use LLMs without them hallucinating
  statistics?": the engine computes, the agent narrates, every number is traced.
- **Clean, tested code** and a clear architecture.

**Deliverables for this track:**
1. The working demo (through M5).
2. A **written case study** (the M7 artifact): the problem, the design decisions, the
   statistics (with the math), the privacy stance, the AI grounding approach, and honest
   limitations. Written in the voice of a senior DS. *This is the single highest-leverage
   artifact for an application.*
3. A short demo video / scripted walkthrough.
4. A clean public README (already drafted).

**Framing note:** present it as a portfolio project that showcases how you'd build
experimentation infrastructure — not as a claim of affiliation. Keep any company name out of
the product itself; it's an audience you're tailoring the *story* to, not a customer.

## Track B — Sellable SaaS
**Goal:** a product data-science / growth teams at larger companies would pay for.

**Who buys:** mid-to-large companies with a real experimentation practice but where a few DS
gate everything (the bottleneck in [`01-product-vision.md`](./01-product-vision.md)).

**Wedge:** "**5–10× more experiments analyzed per data scientist, with rigor increased, not
lowered.**" The AI agents are the wedge; the engine is the moat (trust).

### Competitive landscape & positioning
| Player | Shape | Where Mallard differs |
|---|---|---|
| Optimizely / VWO / Adobe Target | visual editor + testing | we're an engine+brain, not a page builder; far deeper stats; AI-native |
| LaunchDarkly / Split | feature flags (+ some experiments) | we lead with analysis & interpretation, not just flagging |
| Statsig / Eppo | modern, warehouse-native experimentation | **AI agents that do the DS workflow** + privacy-first posture |
| GrowthBook (OSS) | open-source experimentation | AI-native + managed rigor; possible open-core overlap |
| Internal tools (Airbnb/Microsoft/Netflix) | bespoke, not for sale | productized + agentic for teams without a platform org |

**Positioning sentence:** *"The AI-native, privacy-first experimentation platform: agents
design, monitor, analyze, and write up your experiments on top of a statistics engine you can
actually trust — on your own data warehouse."*

### Pricing (hypotheses to test, not commitments)
- **Free / OSS core:** assignment + frequentist stats + dashboard (drives adoption, the
  DuckGrowthBook-style wedge).
- **Pro (per-seat + usage):** advanced stats (CUPED, sequential, Bayesian), AI agents (metered
  by agent runs / tokens), warehouse connectors.
- **Enterprise:** SSO/RBAC, audit, self-host, support, DP/compliance features.
AI usage is a real COGS line → meter it; the model-routing/caching design in
[`05-ai-agents.md`](./05-ai-agents.md) is what keeps margins healthy (and is the same cost pass
you're planning).

### Open-core consideration
An MIT/Apache core (engine + SDK + dashboard) with a commercial layer (AI agents, warehouse
connectors, enterprise/governance) maximizes both adoption *and* the portfolio story (public
code to show), while keeping the differentiator monetizable. Decide before first public push;
tracked in [`10-decisions.md`](./10-decisions.md). Until then: all-rights-reserved.

## Shared: what makes the demo land
1. From a one-paragraph hypothesis to a powered, well-designed experiment in seconds (Designer).
2. A planted data bug caught by the Monitor (SRM) — shows rigor and the "catch the mistake"
   value.
3. CIs visibly tightening when CUPED is toggled — shows statistical sophistication.
4. A generated ship/no-ship readout that's correct and **sourced** — shows grounded AI.
5. No PII anywhere; analysis runnable on the customer's warehouse — shows privacy.

## Metrics to prove value (for either track)
- Experiments analyzed per DS / per week (throughput).
- Time from hypothesis → launch and from stop → readout.
- Rate of caught data-quality issues (SRM) before conclusions.
- Decision accuracy of agents vs. ground truth (from the eval harness).
- AI cost per experiment (margin).
