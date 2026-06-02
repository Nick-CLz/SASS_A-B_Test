# sdks/

Client libraries for assignment + tracking. **Built by `P05`.** Currently a placeholder.

```
sdks/
├── python/        # pip-installable; getVariant/peekVariant/track; local bucketing
├── typescript/    # npm package; usable server-side (Node) and as a thin client
└── fixtures/       # cross-language golden fixtures (salt, unit_id) → bucket/variant  (from P04)
```

## The contract that matters
Both SDKs **bucket locally using the exact same hash construction as the server**
(`backend/app/assignment/`, `docs/04-statistics-engine.md` §Assignment). The shared
`fixtures/` file (produced in `P04`) is the source of truth: each SDK has a test asserting it
reproduces every fixture exactly. If client and server ever disagree on a variant, assignment
is broken.

## Behavior (see `docs/06-api-and-sdk.md` §SDK)
- `getVariant` logs an exposure; `peekVariant` does not (for triggered analysis).
- `track` is batched, non-blocking, and never throws into the host app.
- Privacy guards: pseudonymous `unitId` required; PII-looking attributes/props rejected.
- Resilient defaults: unreachable service → return control, buffer events.
