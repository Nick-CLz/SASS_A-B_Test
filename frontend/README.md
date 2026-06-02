# frontend/

Next.js (App Router) + TypeScript dashboard. **Scaffolded by `P01`, built out by `P10`** (and
shows agent readouts once `P14` lands). Currently a placeholder.

## Planned structure
```
frontend/
├── package.json              # P01 (pnpm)
├── Dockerfile                # P10
├── app/                      # App Router pages
│   ├── page.tsx              # home / health (P01) → experiment list (P10)
│   └── experiments/[key]/    # detail: config | results | health | readout (P10)
├── components/               # shadcn/ui-based components, result cards, SRM banner, charts
├── lib/                      # API client (TanStack Query) against /v1
└── tests/                    # component + smoke e2e
```

## Conventions
- Strict TypeScript, Tailwind, shadcn/ui, TanStack Query, Recharts.
- Honest statistical presentation: **lead with confidence intervals**, show significance only
  after correction, and surface SRM as a loud banner (see `docs/04-statistics-engine.md`).
- Talks only to the documented `/v1` API (`docs/06-api-and-sdk.md`).

## Commands (finalized by P01)
```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm build && pnpm test && pnpm lint
```
