# backend/

FastAPI app + statistics engine + AI agents. **Built by prompts `P01`–`P09`, `P11`–`P15`.**
Currently a placeholder — `P01` creates the project (`pyproject.toml`, `app/`, `Dockerfile`).

## Planned structure (see `docs/02-architecture.md`)
```
backend/
├── pyproject.toml            # P01
├── Dockerfile                # P01
├── alembic/                  # P02 migrations
└── app/
    ├── main.py               # FastAPI app + /v1/health        (P01)
    ├── core/                 # settings, logging               (P01)
    ├── models/               # SQLModel metadata tables        (P02)
    ├── services/             # domain logic (thin)             (P03, P09)
    ├── api/v1/               # REST routers                    (P03, P09, agents)
    ├── assignment/           # PURE deterministic bucketing     (P04)
    ├── ingestion/            # events → analytics + PII guard   (P06)
    ├── analytics/            # AnalyticsBackend adapter (DuckDB) (P06)
    ├── stats/                # PURE stats engine                (P07, P08)
    │   ├── frequentist.py    diagnostics.py  power.py           (P07)
    │   └── variance_reduction.py  sequential.py  bayesian.py  segments.py  (P08)
    └── agents/               # Claude agents + tools + evals    (P11–P14)
```

## Non-negotiables (from `CLAUDE.md`)
- `app/stats/` and `app/assignment/` are **pure** (no I/O, no globals) and tested against golden
  fixtures + calibration simulations.
- `app/agents/` **never computes statistics** — agents call `app/stats/` via tools.
- No PII reaches `app/analytics/` storage (enforced in `app/ingestion/`).

## Commands (finalized by P01)
```bash
uv sync
uvicorn app.main:app --reload
pytest && ruff check . && mypy app
```
