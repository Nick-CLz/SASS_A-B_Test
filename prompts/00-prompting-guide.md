# 00 — Prompting guide (how to drive the build)

You (the human) will paste each `P##` prompt into a model and let it work. This guide makes
that smooth and cheap.

## The loop
1. Open a fresh session (clean context) for each prompt.
2. Paste the prompt's full text. The prompt tells the model what to read in `docs/`.
3. Let it implement + test. It commits when acceptance criteria pass.
4. **You** skim the diff and run the acceptance checks. If good, go to the next prompt.
5. If it stalls or drifts, point it back at the relevant `docs/` file (the source of truth).

## Preamble to prepend to every prompt (recommended)
> You are building "Mallard", an AI-native A/B testing platform. The plan is in `docs/` and is
> the source of truth — read the files this prompt names before coding. Follow `CLAUDE.md`
> conventions. Work only within the scope of this prompt. Write tests, make them pass, then
> commit with a Conventional Commit message. Do not invent statistics in code that an AI agent
> would output — agents call the stats engine as tools (see `docs/05-ai-agents.md`). Ask before
> doing anything destructive.

## Conventions every prompt assumes
- **Docs win.** Code disagreeing with `docs/` is a bug; if a doc is wrong, fix the doc in the
  same change.
- **Test each increment.** Don't commit red. Python: `pytest`; TS: the framework P01 sets up.
- **Conventional Commits:** `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`.
- **Determinism in assignment & stats.** Seed randomness in tests; golden fixtures.
- **No PII** in events/analytics; **no LLM-computed numbers** in agent outputs.
- **Stay in scope.** Each prompt is bounded; resist building ahead.

## Model routing = your main cost lever
Set `AGENT_MODEL_SMALL/MEDIUM/LARGE` in `.env`. For *building* (not runtime), use the same idea:
- **Small model:** scaffolding, boilerplate, wiring, docs, simple CRUD, frontend glue.
- **Medium model:** most application logic, APIs, SDKs, dashboard, the agent prompts.
- **Large model:** **assignment (P04)** and **statistics (P07, P08)** and the **agent
  foundation (P11)** — correctness-critical or architecturally load-bearing. A subtle bug here
  silently invalidates every downstream result, so the marginal model cost is cheap insurance.

Rule of thumb: **spend on correctness, save on boilerplate.** If the budget is very tight, run
everything on a medium model *except* P04/P07/P08, and have a large model *review* those diffs.

## Runtime cost levers (for the agent layer, P11–P14)
These are also where your separate cost-optimization pass should focus:
- Prompt caching on stable system prompts + experiment/data context.
- Route each agent task to the smallest model that passes its eval (P11 sets up evals).
- Token budgets + step caps per agent run; record `cost_tokens`.
- Batch non-interactive jobs (nightly Monitor sweeps) via the Batch API.

## Keeping context small (helps cheap models)
- One prompt per session.
- Tell the model to read only the `docs/` files the prompt names, plus the code it's editing.
- Prefer many small, tested commits over one giant change.
- If a prompt says "If you must split this," follow that split on a smaller model.

## Definition of done for a prompt
- All acceptance criteria pass (you verified, not just the model's word).
- Tests added and green; lint/type-check clean.
- Docs updated if behavior changed.
- A clean Conventional Commit (or a few) on the branch.

## If something's ambiguous
The model should choose the option most consistent with `docs/`, note the assumption in the
commit body, and keep going — not stall. You can correct course at the diff review.
