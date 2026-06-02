# P10 — Dashboard (M3)

**Goal:** a clean Next.js dashboard to create/run experiments and read results with proper
statistical presentation. This is what a reviewer (or buyer) actually sees — make it sharp.

**Read first:** `docs/06-api-and-sdk.md` (the API it consumes), `docs/04-statistics-engine.md`
(how to present CIs/significance/SRM honestly), `docs/01-product-vision.md` (personas/tone).
Builds on P03 + P09 (and shows agent output once P12–P14 land).

## Deliverables (in `frontend/`)
- **Experiment list:** status, owner, OEC, last analyzed; filter by status/workspace.
- **Experiment detail:**
  - config tab (variants, allocations, metrics + roles, targeting, layer),
  - **results tab:** per-metric cards showing estimate, **absolute + relative lift with CIs**,
    significance (after correction), sample sizes; lead with the interval, not just a p-value;
  - **SRM banner:** a loud, unmissable warning when SRM is flagged ("results not trustworthy").
  - **time series:** metric-by-day (novelty check); sequential interval view when available.
  - **power calculator:** sample size / MDE / runtime widget.
  - a CUPED toggle that visibly tightens CIs (once P08 is wired).
- **Create/edit experiment** form with client-side validation mirroring the API invariants.
- Data fetching via TanStack Query against `/v1`; charts via Recharts; UI via shadcn/ui +
  Tailwind. Loading/empty/error states. Accessible, responsive.
- A spot on the detail page reserved for the **agent readout** (filled when P14 lands).
- Tests: component tests for the results presentation (CI rendering, SRM banner appears when
  flagged) and a smoke e2e of the create→view flow against a running API (or mocked).

## Acceptance criteria
- The full M2 flow is usable in the browser: create experiment → (synthetic events ingested) →
  analyze → see results with CIs, significance, and SRM handling.
- SRM banner appears exactly when the API flags it; significance reflects correction.
- `pnpm build`, `pnpm test`, `pnpm lint` all green.
- Honest stats presentation (intervals first; no "99% significant!" theater).

## Notes
- Visual polish matters for both audiences (portfolio + sales). Keep it clean and trustworthy,
  not flashy. Dark/light is fine; consistency and clarity over decoration.

## If you must split this
List + detail/results first (the demo core), then create/edit form, then power calculator and
charts.

## Commit
`feat: dashboard list/detail/results`, etc. Suggested model: **medium**.
