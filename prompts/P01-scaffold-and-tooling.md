# P01 — Scaffold & tooling (M0)

**Goal:** turn the planned repo into a runnable skeleton with all toolchains, CI, and a health
endpoint. No business logic yet.

**Read first:** `README.md`, `CLAUDE.md`, `docs/02-architecture.md` (component layout),
`.env.example`, `infra/docker-compose.yml`.

## Deliverables
### Backend (`backend/`)
- Python 3.12 project managed with `uv` (or Poetry): `pyproject.toml` with deps `fastapi`,
  `uvicorn`, `pydantic`, `pydantic-settings`, `sqlmodel`, `alembic`, `psycopg`, `numpy`,
  `scipy`, `statsmodels`, `pandas`, `duckdb`, `anthropic`; dev deps `pytest`, `pytest-cov`,
  `ruff`, `mypy` (or `pyright`), `httpx`.
- App package `app/` with the structure from `docs/02-architecture.md`:
  `app/main.py` (FastAPI), `app/api/`, `app/assignment/`, `app/ingestion/`, `app/analytics/`,
  `app/stats/`, `app/agents/`, `app/models/`, `app/services/`, `app/core/` (settings, logging).
- `app/core/config.py`: Pydantic settings reading `.env` (the vars in `.env.example`).
- `GET /v1/health` → `{ "status": "ok", "version": ... }`.
- `Dockerfile` (referenced by `infra/docker-compose.yml`).
- `ruff`, `mypy`, `pytest` configured; one passing test for `/v1/health`.

### Frontend (`frontend/`)
- Next.js (App Router) + TypeScript + Tailwind, `pnpm`. shadcn/ui initialized. TanStack Query +
  Recharts installed. ESLint + Prettier. A placeholder home page that calls `/v1/health` and
  shows the status. One passing component/test (Vitest or Playwright smoke).

### Repo-wide
- CI (`.github/workflows/ci.yml`): on push/PR, run backend lint+type+test and frontend
  lint+build+test. Must be green on this scaffold.
- Update `CLAUDE.md` "Commands" section with the real commands.
- A top-level `Makefile` or `justfile` with `setup`, `dev`, `test`, `lint` targets.

## Acceptance criteria
- `cd backend && uv sync && pytest` → green; `ruff check .` and `mypy app` (or pyright) clean.
- `uvicorn app.main:app` then `GET /v1/health` → 200 `{status: ok}`.
- `cd frontend && pnpm install && pnpm build` succeeds; `pnpm test` green; `pnpm dev` shows the
  health status from the backend.
- `docker compose -f infra/docker-compose.yml up db` starts Postgres; `--profile full` builds
  api + web.
- CI workflow is green.

## If you must split this
Commit backend scaffold first (feat: scaffold backend), then frontend (feat: scaffold
frontend), then CI (chore: ci). Each independently green.

## Commit
Conventional commits per the above. Suggested model: **small**.
