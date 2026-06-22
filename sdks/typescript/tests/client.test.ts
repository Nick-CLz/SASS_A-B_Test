import { describe, expect, it } from "vitest";

import { Mallard } from "../src/client";
import type { ExperimentSpec } from "../src/types";

const SPEC: ExperimentSpec = {
  key: "checkout",
  salt: "checkout",
  trafficPct: 100,
  variants: [
    { key: "control", allocationPct: 70 },
    { key: "treatment", allocationPct: 30 },
  ],
};

describe("client", () => {
  it("logs an exposure on getVariant and queues track events", () => {
    const m = new Mallard({ flushAt: 1000 });
    m.loadSpecs([SPEC]);
    const a = m.getVariant("checkout", "user-1");
    expect(a.inExperiment).toBe(true);
    m.track("user-1", "purchase", 9.99, { sku_count: 1 });
    expect(m.pending).toBe(2); // 1 exposure + 1 event
  });

  it("peekVariant does not log an exposure", () => {
    const m = new Mallard({ flushAt: 1000 });
    m.loadSpecs([SPEC]);
    m.peekVariant("checkout", "user-1");
    expect(m.pending).toBe(0);
  });

  it("returns unknown_experiment for an unloaded key", () => {
    const m = new Mallard();
    expect(m.getVariant("missing", "user-1").reason).toBe("unknown_experiment");
  });

  it("flush to an unreachable server does not throw and keeps the queue", async () => {
    const m = new Mallard({ baseUrl: "http://127.0.0.1:1", flushAt: 1000 });
    m.loadSpecs([SPEC]);
    m.track("user-1", "view");
    await expect(m.flush()).resolves.toBeUndefined();
    expect(m.pending).toBe(1); // kept for retry
  });
});
