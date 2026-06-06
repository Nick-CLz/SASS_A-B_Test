# Mallard TypeScript SDK

Deterministic, **local** experiment assignment + privacy-guarded, resilient event tracking.
Usable server-side (Node) or as a thin client. Bucketing is byte-for-byte identical to the
Mallard server and the Python SDK — all three are tested against the shared
[`../fixtures/bucketing.json`](../fixtures/bucketing.json) golden file.

## Quickstart
```ts
import { Mallard, type ExperimentSpec } from "mallard-sdk";

const checkout: ExperimentSpec = {
  key: "checkout",
  salt: "checkout",
  trafficPct: 100,
  variants: [
    { key: "control", allocationPct: 50 },
    { key: "treatment", allocationPct: 50 },
  ],
};

const mallard = new Mallard({ baseUrl: "http://localhost:8000" });
mallard.loadSpecs([checkout]);

const a = mallard.getVariant("checkout", userId, { country: "US" });
if (a.variantKey === "treatment") {
  // ...show the treatment
}

mallard.track(userId, "purchase", 42.0, { sku_count: 3 });
await mallard.flush();
```

## Behavior
- **Local assignment** — `getVariant` buckets locally (no network on the hot path); falls back to
  `unknown_experiment` if the spec wasn't loaded.
- **Exposures** — `getVariant` logs an exposure by default; `peekVariant` does not (for triggered
  analysis).
- **Privacy** — a pseudonymous `unitId` is required; PII-looking attribute/property keys or
  email-valued strings are rejected client-side (the server enforces the allow-list authoritatively).
- **Resilience** — `track` batches; `flush` is best-effort and never throws into the host app
  (an unreachable service keeps the queue for the next retry).

## Develop
```bash
pnpm install
pnpm test        # vitest: parity (vs fixtures) + privacy + client
pnpm typecheck   # tsc --noEmit
pnpm build       # tsc -> dist/
```

The single source of truth for bucketing is the hash construction documented in
[`docs/04-statistics-engine.md`](../../docs/04-statistics-engine.md#assignment) and pinned by the
golden fixtures; if this SDK ever disagrees with the server on a variant, assignment is broken.
