# Deploy

Mallard ships as two containers (API + dashboard) plus Postgres; analytics is DuckDB by
default (or a warehouse). Everything is configured via env vars — see `.env.example`.

## Try it with zero infra
```bash
make demo                 # full pipeline on in-memory SQLite + DuckDB; no Postgres/Docker
```

## Local stack (Docker)
```bash
cp .env.example .env      # set APP_SECRET_KEY; ANTHROPIC_API_KEY only if using agents
docker compose -f infra/docker-compose.yml up            # db only
docker compose -f infra/docker-compose.yml --profile full up   # db + api + web
# then run migrations against the db:
cd backend && DATABASE_URL=postgresql+psycopg://mallard:mallard@localhost:5432/mallard \
  uv run alembic upgrade head
```
- API: http://localhost:8000 (`/docs` for OpenAPI) · Dashboard: http://localhost:3000
- Point the dashboard at a workspace with `NEXT_PUBLIC_WORKSPACE_ID`.

## Production (any container host: Fly.io / Render / ECS / k8s)
1. **Postgres**: provision a managed instance; set `DATABASE_URL`.
2. **Migrate**: run `alembic upgrade head` on deploy (release command / init job).
3. **API image**: build `backend/Dockerfile`; set `APP_ENV=production`, `APP_SECRET_KEY`,
   `DATABASE_URL`, `DUCKDB_PATH` (or warehouse connector), and `ANTHROPIC_API_KEY` if agents
   are enabled. Expose port 8000.
4. **Dashboard image**: build `frontend/Dockerfile`; set `NEXT_PUBLIC_API_BASE_URL` to the API
   URL. Expose port 3000.
5. **Analytics at scale**: keep DuckDB for small/medium, or implement the warehouse
   `AnalyticsBackend` adapter (BigQuery/Snowflake/Databricks) so computation runs in the
   customer's warehouse.

## Secrets & safety
- Never commit `.env` (gitignored). Inject secrets via the host's secret manager.
- Rotate `APP_SECRET_KEY` and API keys; API keys are stored hashed.
- No PII reaches the analytics store (enforced by the ingestion guard + tests).

## CI
`.github/workflows/ci.yml` runs backend (ruff/mypy/pytest), frontend (lint/test/build), and the
SDK parity suites on every push and PR. Build/publish images from CI as a follow-up step.
