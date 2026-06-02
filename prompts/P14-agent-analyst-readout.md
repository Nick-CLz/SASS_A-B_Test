# P14 — Analyst + Readout agents (M5)

**Goal:** the payoff — run the correct analysis, interpret it, and write a stakeholder-ready,
**sourced** ship/no-ship readout. Humans make the final call.

**Read first:** `docs/05-ai-agents.md` §"Analyst"/"Readout", `docs/04-statistics-engine.md`
(all methods + the fixed-vs-sequential UX rule), `docs/03-data-model.md` (`readout`,
`metric_result`). Builds on P11 + P07 + P08 + P09.

## Deliverables
### Analyst agent
- Tools: `run_analysis` (P09 pipeline), `check_srm`, `get_cuped_adjustment`, `apply_correction`,
  `segment_breakdown`, plus sequential/Bayesian readers (P08).
- System prompt: **SRM first** (if mismatched, stop and report untrustworthy); choose the right
  method per metric; respect the fixed-vs-sequential rule; apply correction; interpret effects
  with caveats (novelty, dilution, Simpson's paradox). Every claim sourced.
- Output: an interpreted results object referencing `metric_result` rows.

### Readout agent
- Tools: reads the Analyst output + result rows; `publish_readout`.
- System prompt: write like a senior DS — TL;DR, **decision recommendation**
  (ship/no-ship/iterate/inconclusive) with confidence, the evidence (effects + CIs), caveats,
  next steps; plain language; every number sourced to a result row.
- Output: a `readout` row (markdown + `decision_recommendation` + `sources`); surfaced in the
  dashboard (the P10 reserved slot).
- Endpoints `POST /v1/experiments/{key}/agents/analyst` and `.../readout`.

## Acceptance criteria
- On synthetic data with a **known** effect, the Analyst recovers it and the Readout's
  recommendation matches ground truth across an eval suite (track decision accuracy).
- On **SRM-injected** data, both refuse to conclude and say results are untrustworthy.
- **Grounding:** every number in the readout traces to a `metric_result`/tool result (harness
  green); a planted unsourced number fails the eval.
- Readout is readable and correct; persisted, immutable, shown in the UI.
- Endpoints + evals green.

## Notes
- This closes the end-to-end demo (`docs/07` M5): hypothesis → design → monitor catches a bug →
  analyze (sequential + CUPED) → sourced readout. Rehearse that path.
- The readout's quality is a headline portfolio artifact — invest in the prompt.

## Commit
`feat: analyst agent`, `feat: readout agent + ui surface`. Suggested model: **medium**.
