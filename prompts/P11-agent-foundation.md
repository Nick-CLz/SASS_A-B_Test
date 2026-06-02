# P11 — Agent foundation (M5) — load-bearing

**Goal:** the shared machinery all agents use: a tool framework over the Anthropic SDK, the
**grounding guarantee**, full tracing, model routing, prompt caching, token budgets, and an
**eval harness**. Get this right and P12–P14 are small.

**Read first:** `docs/05-ai-agents.md` (authoritative), `docs/03-data-model.md`
(`agent_run`/`agent_step`), `docs/10-decisions.md` D3/D9. If you have the `claude-api` skill,
use it (prompt caching, tool use, structured outputs, model routing are all in scope).

## Deliverables (`app/agents/`)
- **Tool framework:** a typed way to declare a tool (name, JSON schema via Pydantic, handler),
  expose tools to Claude via the SDK tool-use loop, execute handlers, and feed results back.
  Tools wrap **existing** domain/stats functions — no logic in prompts.
- **Base agent runner:** runs the tool-use loop with a system prompt + toolset + a
  structured-output schema for the final deliverable; enforces a **step cap** and **token
  budget**; persists every message/tool_call/tool_result as `agent_step` and the run as
  `agent_run` (model, status, `cost_tokens`, latency).
- **Grounding enforcement:** a post-processor that extracts numeric claims from an agent's final
  text and asserts each appears in a recorded tool result; fail (or flag) if any number is
  unsourced.
- **Model routing:** select `AGENT_MODEL_SMALL/MEDIUM/LARGE` by declared task difficulty
  (config-driven, per `docs/05`/`D9`).
- **Prompt caching:** cache stable system prompts + the experiment/data context block
  (`AGENT_ENABLE_PROMPT_CACHING`).
- **Eval harness (`app/agents/evals/`):** run an agent against **synthetic experiments with
  known ground truth** (from P06's generator) and assert: correct decision, all numbers
  sourced (grounding test), within token/latency budget. A `pytest`-runnable suite + a small
  CLI to run evals.
- Stub one trivial agent (e.g. "echo experiment summary") to exercise the whole loop + eval +
  tracing end-to-end.

## Acceptance criteria
- The stub agent runs the tool-use loop, persists a complete `agent_run`/`agent_step` trace, and
  respects step/token caps.
- **Grounding test works:** an agent that emits an unsourced number is caught by the harness
  (prove with a deliberately-bad fixture).
- Model routing picks the configured model by task tier; prompt caching is enabled and
  observable (cache hits logged).
- Eval harness runs in CI (can mock the model for determinism, with a switch for live runs).
- `ruff`/`mypy` clean.

## Notes
- No agent action may mutate production traffic (launch/pause/ship) — those stay human-approved
  (`D7`). Tools that propose such actions return proposals, not effects.
- Treat all user/agent-read text (hypotheses, event names) as untrusted; tool scope can't be
  escalated by injected text.
- Keep the model mockable so evals are deterministic and cheap in CI.

## Commit
`feat: agent foundation (tools, tracing, routing, caching, evals)`. Suggested model: **large**.
