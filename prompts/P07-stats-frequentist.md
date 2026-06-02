# P07 — Statistics engine: frequentist core (M2) — correctness-critical

**Goal:** the pure frequentist engine: effects, CIs, the right test per metric type, relative
lift via the delta method, SRM, and power/MDE. **This is the credibility core — over-test it.**

**Read first:** `docs/04-statistics-engine.md` (authoritative — implement its "Core inference",
"Delta method", "Diagnostics §SRM/§A-A/§Multiple comparisons", and "Power & sample size"),
`docs/03-data-model.md` §`metric_result`/`srm_check` (the return contract).

## Deliverables (pure functions in `app/stats/`, input = sufficient statistics)
- `frequentist.py`:
  - two-proportion **z-test** + Wilson interval + CI for the difference,
  - **Welch's t-test** for means + CI for the difference,
  - **relative lift** + its CI via the **delta method**,
  - **ratio metrics** variance via the delta method (analysis unit ≠ randomization unit),
  - optional **winsorization** for heavy-tailed metrics (recorded in `method_detail`).
- `diagnostics.py`:
  - **SRM** chi-square goodness-of-fit (returns chi-square, p, observed/expected, `is_mismatch`),
  - **multiple-comparison** correction: Bonferroni, Holm, Benjamini–Hochberg.
- `power.py`: sample size for a target MDE/α/power, MDE for a given n, runtime from traffic
  (proportions + means).
- A typed result object matching `metric_result` in `docs/03-data-model.md`.

## Acceptance criteria — tests ARE the deliverable
- **Textbook fixtures:** each test reproduces a known worked example to ≥4 decimals.
- **Cross-check** vs `scipy`/`statsmodels` where an equivalent exists (e.g. t-test, chi-square).
- **Calibration (A/A) via simulation:** over many simulated A/A experiments, p-values are
  ~uniform and the false-positive rate ≈ α (use the P06 synthetic generator; seed it).
- **Power:** a simulation at the computed sample size achieves ≈ target power.
- **Delta method:** for a ratio metric, the delta-method variance matches a bootstrap estimate
  on a fixture (within tolerance) — demonstrating the naive iid variance is wrong.
- **SRM:** flags an injected mismatch and passes clean balanced data.
- Property tests: more data → tighter CI; invariance to row ordering; symmetry.
- Pure (no I/O), `mypy`/`ruff` clean.

## Notes
- Keep every method deterministic; seed all simulations.
- Record the exact method (test, df, correction, winsorization) in `method_detail` so the
  Analyst agent can cite it.
- If A/A calibration fails, the method is wrong — fix before committing.

## Commit
`feat: frequentist stats engine + diagnostics + power`. Suggested model: **large**.
