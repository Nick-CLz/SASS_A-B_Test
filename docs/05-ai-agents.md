# 05 — AI agent layer

This is the headline feature: **AI agents that take over the patterned parts of the data
scientist's job.** It is also where the project's "AI takes over this work" thesis lives.

## The one rule that makes it trustworthy
**Agents never compute or invent statistics. They call the engine as tools and narrate the
results.** Every number in an agent's output is traceable to a recorded tool call
(`agent_step` rows in [`03-data-model.md`](./03-data-model.md)). If a number can't be traced to
a tool result, it's a bug, and a test should catch it.

This grounding is the difference between a credible product and a demo that hallucinates
p-values. It's also the strongest answer to "why trust an LLM with statistics?" — *we don't;
we trust the engine, and the LLM operates it.*

## The agents
Each agent = a **system prompt** + a **toolset** (functions into domain services and the stats
engine) + a **structured-output schema** for its deliverable. They run as a small orchestration
inside `backend/app/agents/`.

### 1. Designer agent — "turn a hypothesis into a sound experiment"
- **Input:** a product hypothesis in plain language (+ context: surface, audience, baseline
  rates if known).
- **Does:** proposes randomization unit, OEC + secondary + guardrail metrics, variants, target
  MDE, and — via the `power_analysis` tool — a defensible sample size and runtime. Flags
  underpowered or ill-posed designs.
- **Tools:** `list_metrics`, `get_baseline_rates`, `power_analysis`, `propose_experiment_config`
  (writes a draft `experiment` + `variant` rows), `find_related_experiments` (Memory).
- **Output (structured):** a complete draft experiment config + a rationale. Human reviews and
  approves before launch.

### 2. Health Monitor agent — "catch the data bug before it ruins the readout"
- **Runs:** on a schedule / on new data while an experiment is `running`.
- **Does:** checks **SRM**, sample sizes vs. plan, guardrail breaches, ingestion anomalies,
  novelty drift. Raises alerts; can *recommend* (not execute) a pause.
- **Tools:** `check_srm`, `get_guardrail_status`, `get_exposure_counts`, `detect_anomalies`,
  `recommend_pause`.
- **Output:** a health status + ranked alerts. Pausing requires human (or explicit policy)
  approval.

### 3. Analyst agent — "run the right test and interpret it"
- **Does:** picks the correct method per metric type, runs frequentist + Bayesian + sequential
  as configured, checks SRM **first**, applies multiple-comparison correction, runs
  pre-registered segment breakdowns, and interprets — including caveats (novelty, dilution,
  Simpson's paradox).
- **Tools:** `run_analysis`, `check_srm`, `segment_breakdown`, `apply_correction`,
  `get_cuped_adjustment`. (All call `backend/app/stats`.)
- **Output:** an interpreted results object (sourced to result rows) + flagged risks.

### 4. Readout Writer agent — "write what a senior DS would write"
- **Does:** composes a stakeholder-ready readout: TL;DR, the decision recommendation
  (ship / no-ship / iterate / inconclusive) with confidence, the evidence (effects + CIs),
  caveats, and next steps — in plain language, sourced to the Analyst's results.
- **Tools:** reads the Analyst output + result rows; `publish_readout`.
- **Output:** `readout` row (markdown + `decision_recommendation` + `sources`). Immutable once
  published.

### Stretch agents
- **Reviewer:** pre-launch design critique (peeking risk, underpowered, bad OEC, too many
  metrics without correction).
- **Memory:** institutional memory — links related past experiments, surfaces priors, prevents
  re-running known experiments.

## Orchestration
- **Human-in-the-loop by default.** Agents *propose, monitor, analyze, and recommend*; humans
  *approve* launches, pauses, and ship decisions. This is a product principle, not a limitation.
- **Designer → (human approve) → run → Monitor (loop) → Analyst → Readout → (human decide).**
- A lightweight orchestrator coordinates; no heavyweight agent framework needed for the MVP
  (FastAPI + the Anthropic SDK's tool-use loop is enough). Keep each agent single-purpose.

## How tools are implemented
- Each tool is a thin, typed Python function with a JSON schema (Pydantic) exposed to Claude
  via the SDK's tool-use API.
- Tools wrap **existing** domain/stats functions — no business logic lives in the agent prompt.
- Every tool call + result is persisted as an `agent_step` for audit and for the "no invented
  numbers" guarantee.
- Tools are deterministic and individually unit-tested *without* the LLM, so agent behavior is
  separable from tool correctness.

## Model routing & cost (ties directly to your cost-optimization pass)
Route by task difficulty; this is where most of the spend is decided.
| Task | Default model | Why |
|---|---|---|
| Health checks, classification, formatting | `AGENT_MODEL_SMALL` (Haiku) | cheap, high-volume, easy |
| Analysis interpretation, readout drafting | `AGENT_MODEL_MEDIUM` (Sonnet) | solid reasoning, good writing |
| Hard experiment design, ambiguous tradeoffs | `AGENT_MODEL_LARGE` (Opus) | deepest reasoning, rarer calls |

Cost levers (build these in from the start):
- **Prompt caching** for the (large, stable) system prompts and the experiment/data context →
  big savings on multi-step agent runs. (`AGENT_ENABLE_PROMPT_CACHING`.)
- **Structured outputs / tool-forced** responses to avoid wandering.
- **Token budgets & step caps** per agent run, recorded in `agent_run.cost_tokens`.
- **Batch** non-interactive jobs (e.g. nightly Monitor sweeps) via the Batch API.
- Make the model IDs **config**, not hardcoded, so your cheaper-model pass can re-route freely.

## Evaluation harness (don't skip — this is how you prove it works)
- **Synthetic experiments with known ground truth:** generate data where the true effect, SRM
  presence, and best decision are known; assert the agents reach the right call.
- **Grounding test:** parse every number in an agent's output and assert it appears in a tool
  result. Fail the eval if any number is unsourced.
- **Decision accuracy:** ship/no-ship vs. ground truth across a suite; track precision/recall.
- **Regression suite:** freeze prompts + a fixture set; alert on behavior drift.
- **Cost/latency budget:** track tokens and time per agent; fail if over budget.

## Safety & guardrails
- No agent action mutates production traffic without human/policy approval (launch, pause,
  ship).
- Agents operate only within an org/workspace scope (tenant isolation).
- All inputs the agent reads (hypotheses, event names) are treated as untrusted text;
  prompt-injection in user content can't escalate tool scope.
- The audit trail (`agent_run`/`agent_step`) is immutable and reviewable.

## Why this is the differentiator
Feature-flag vendors bolt a chatbot on the side. Mallard inverts it: the agents *operate the
platform* through the same audited tools a human would use, grounded in a real stats engine.
That's defensible, demoable, and exactly the "AI does the DS job" story — without the
hallucination risk that sinks naive LLM-stats products.
