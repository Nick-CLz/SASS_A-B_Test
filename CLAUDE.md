# CLAUDE.md — context for the agent building Mallard

This file is read automatically by Claude Code (and is useful context for any model) doing
the build. Keep it short and current. The full plan lives in [`docs/`](./docs/); the build
steps live in [`prompts/`](./prompts/).

## What this project is
Mallard is an AI-native, privacy-first **A/B testing & experimentation platform** for
data-science teams. The headline feature is a set of **AI agents** that design, monitor,
analyze, and write up experiments by *calling the deterministic stats engine as tools* —
they never compute or invent statistics themselves.

## Golden rules for the build
1. **Docs are the source of truth.** If a prompt and the code disagree, re-read the relevant
   `docs/` file. If a doc is wrong, fix the doc in the same change.
2. **Agents never do math.** Any number an AI agent reports must come from a tool call into
   the stats engine (`backend/stats/`). No LLM-computed p-values, ever. See `docs/05-ai-agents.md`.
3. **Privacy first.** No PII (emails, names, IPs, raw addresses) in the event stream or
   analytics store. Units are pseudonymous IDs. See `docs/01-product-vision.md`.
4. **Determinism where it counts.** Assignment (bucketing) and statistics must be pure,
   deterministic, and unit-tested against known fixtures. Seed every random process in tests.
5. **Test every increment.** Each prompt ends with acceptance criteria and tests. Don't
   commit until they pass. Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).

## Conventions
- **Python:** 3.12, FastAPI, Pydantic v2, SQLModel. Format/lint with `ruff`; type-check with
  `mypy` or `pyright`. Tests with `pytest`. Keep the stats engine pure (no I/O, no globals).
- **TypeScript/Frontend:** Next.js App Router, strict TS, Tailwind + shadcn/ui, TanStack
  Query for data fetching, Recharts for charts. ESLint + Prettier.
- **API:** versioned under `/v1`. OpenAPI is generated from FastAPI; the TS SDK is generated
  or hand-written against it. See `docs/06-api-and-sdk.md`.
- **Layout:** `backend/`, `frontend/`, `sdks/`, `infra/`. Each has a README describing its
  internal structure.

## Commands (filled in by P01)
```bash
# backend
cd backend && uv sync && uvicorn app.main:app --reload       # run API
cd backend && pytest                                          # tests
cd backend && ruff check . && mypy app                        # lint + types
# frontend
cd frontend && pnpm install && pnpm dev                       # run dashboard
# everything (local)
docker compose up                                             # postgres + api + web
```

## Where to look
- New to the project? Read `docs/00-overview.md` → `docs/02-architecture.md`.
- Building a feature? Find its prompt in `prompts/` and open the docs it references.
- Statistics questions? `docs/04-statistics-engine.md` and `docs/09-glossary.md`.
