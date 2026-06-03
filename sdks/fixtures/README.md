# Cross-language fixtures

`bucketing.json` is the **assignment contract**. The Python backend (`backend/app/assignment`)
and every SDK (`sdks/python`, `sdks/typescript` — built in P05) must reproduce its values
exactly, so client-side and server-side bucketing never disagree.

- `bucket[]` — `(salt, unit_id) → bucket` in `[0, 1)`.
- `assignment_spec` + `assignment[]` — `unit_id → variant_key` for a 70/30 experiment.

The hash construction is documented in `backend/app/assignment/bucketing.py` and
`docs/04-statistics-engine.md#assignment`. The backend test `tests/test_assignment.py`
asserts the engine matches this file; the SDK parity tests (P05) will load the same file.
