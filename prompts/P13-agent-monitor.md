# P13 — Health Monitor agent (M5)

**Goal:** continuously watch a running experiment for data-quality problems and guardrail
breaches, raise ranked alerts, and *recommend* (never execute) a pause.

**Read first:** `docs/05-ai-agents.md` §"Health Monitor agent", `docs/04-statistics-engine.md`
§Diagnostics (SRM, novelty), `docs/07-roadmap.md` (the planted-bug demo moment). Builds on
P11 + P07/P09.

## Deliverables
- A `MonitorAgent` with tools: `check_srm`, `get_guardrail_status`, `get_exposure_counts`,
  `detect_anomalies` (e.g. sudden volume drops, missing variants, novelty drift), and
  `recommend_pause` (returns a proposal, not an action — `D7`).
- System prompt: check SRM first; assess sample accrual vs. plan; check guardrails; rank alerts
  by severity; explain each in plain language and **cite the tool result**.
- Runnable on demand (`POST /v1/experiments/{key}/agents/monitor`) and as a scheduled/batch
  sweep (note how it'd be wired to a scheduler; batch via the Batch API per `docs/05` cost
  notes).
- Output: a health status (`healthy`/`warn`/`critical`) + ranked, sourced alerts; persisted.
- Evals: on synthetic experiments with an **injected SRM** and an injected guardrail breach,
  assert the agent flags them at the right severity and recommends a pause for `critical`;
  assert clean data yields `healthy` (no false alarms).

## Acceptance criteria
- Detects and correctly ranks an injected SRM and a guardrail regression; stays quiet on clean
  data.
- `recommend_pause` returns a proposal only; no traffic mutation happens.
- All alert numbers sourced to tools (grounding green).
- Endpoint + evals green; trace persisted.

## Notes
- This agent powers the most persuasive demo beat (catching a planted bug) — make its output
  crisp and its severity logic defensible.

## Commit
`feat: health monitor agent + endpoint + evals`. Suggested model: **medium**.
