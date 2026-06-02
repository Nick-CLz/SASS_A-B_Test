# P12 — Designer agent (M5)

**Goal:** turn a plain-language hypothesis into a sound, powered experiment design (draft), with
a human approving before launch.

**Read first:** `docs/05-ai-agents.md` §"Designer agent", `docs/04-statistics-engine.md` §Power,
`docs/03-data-model.md` (experiment/variant/metric). Builds on P11 + P07 (power) + P03 (CRUD).

## Deliverables
- A `DesignerAgent` on the P11 foundation with tools:
  `list_metrics`, `get_baseline_rates` (from analytics), `power_analysis` (P07),
  `propose_experiment_config` (writes a **draft** experiment + variants + metric roles via the
  P03 services), and (if available) `find_related_experiments`.
- System prompt encoding the rigor checklist from `docs/01`/`docs/04`: pick a randomization
  unit, one OEC + guardrails, a defensible MDE, and compute sample size/runtime via the tool
  (never guessed). Flags underpowered or ill-posed hypotheses.
- Structured output: a complete draft config + a written rationale, returned and persisted; the
  experiment is created in `draft` (human approves transition to `running`, per `D7`).
- Endpoint `POST /v1/experiments/{key}/agents/designer` (or a create-from-hypothesis variant).
- Evals (extend P11 harness): given hypotheses with known sensible designs, assert the agent
  proposes an appropriate unit/OEC/guardrails and a **sample size that came from the tool**
  (grounding), and flags an underpowered ask.

## Acceptance criteria
- From a one-paragraph hypothesis, produces a complete, valid draft experiment (passes P03
  invariants) with a tool-computed sample size/runtime.
- Refuses/flags ill-posed or underpowered designs with a clear reason.
- All numbers sourced to tool calls (grounding test green).
- Endpoint + evals green; trace persisted.

## Commit
`feat: designer agent + endpoint + evals`. Suggested model: **medium**.
