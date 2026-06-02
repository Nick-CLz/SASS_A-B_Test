# P16 — Demo data, deploy & case study (M7)

**Goal:** make it effortless to *show* — a seeded demo, a one-command run, a deployable image,
and the written case study that is the highest-leverage portfolio artifact.

**Read first:** `docs/07-roadmap.md` M7, `docs/08-go-to-market.md` (both tracks + "what makes
the demo land"), `README.md`. Builds on everything.

## Deliverables
- **Seed + scripted demo:** a `make demo` (or script) that spins up the stack, seeds a realistic
  multi-experiment dataset via the P06 synthetic generator — including one experiment with an
  **injected SRM** and one with a strong CUPED covariate — and prints a walkthrough of the
  end-to-end story (hypothesis → Designer → Monitor catches SRM → Analyst with sequential+CUPED
  → sourced Readout).
- **Deploy:** production Dockerfiles + a deploy config for a container host (Fly.io/Render or
  similar) + a `docs/deploy.md`. Env via `.env`; secrets documented, never committed. CI builds
  and (optionally) publishes images.
- **Case study (`docs/case-study.md`):** the portfolio/interview artifact, in the voice of a
  senior data scientist: problem framing, the design decisions and tradeoffs, the **statistics**
  (with the math — delta method, CUPED, sequential, SRM), the **privacy-first** stance, the
  **grounded-AI** approach (and why it doesn't hallucinate stats), results from the demo, and
  honest limitations + what you'd do next.
- **Polish pass:** README screenshots/GIF, a short demo-video script, and a final tidy of
  `docs/` so the public story is coherent. Confirm the **name/license** decisions in
  `docs/10-decisions.md` are reflected everywhere (the "D-Naming" checklist).

## Acceptance criteria
- One command brings up a fully seeded, explorable instance; the scripted demo runs the whole
  M5 story end-to-end without manual data setup.
- The app deploys to the chosen host from the documented steps.
- `docs/case-study.md` is complete, correct, and reads like a strong DS write-up (it can be sent
  to an employer as-is).
- No PII anywhere in the seeded data; every demo number traces to a tool call.

## Notes
- This is where the two audiences diverge: for the portfolio, the **case study + demo** are the
  deliverable; for SaaS, the **deploy + onboarding** are. Do both; they share the seed/demo.

## Commit
`feat: seed + demo script`, `chore: deploy config`, `docs: case study`. Suggested model: **medium**.
