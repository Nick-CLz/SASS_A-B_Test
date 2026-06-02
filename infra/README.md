# infra/

Local dev + deployment configuration.

```
infra/
├── docker-compose.yml   # local stack: Postgres (now) + api + web (after P01/P10)   [present]
└── deploy/               # production deploy config (Fly.io/Render/…)               (P16)
```

## Local development
```bash
# from repo root
docker compose -f infra/docker-compose.yml up db          # just Postgres (works now)
docker compose -f infra/docker-compose.yml --profile full up   # + api + web (after P01/P10)
```
`db` exposes Postgres on `localhost:5432` (`mallard`/`mallard`/`mallard`). Set `DATABASE_URL`
in `.env` (see `.env.example`).

## Deployment
Production Dockerfiles + a container-host deploy config and `docs/deploy.md` are produced in
`P16`. CI lives in `.github/workflows/` (created in `P01`).
