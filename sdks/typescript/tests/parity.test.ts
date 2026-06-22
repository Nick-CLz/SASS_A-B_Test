// Cross-language parity: the TS SDK must reproduce the shared golden fixtures exactly
// (the same file the Python SDK and the server are tested against).

import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { bucket } from "../src/bucketing";
import { assign } from "../src/engine";
import type { ExperimentSpec } from "../src/types";

interface Fixtures {
  bucket: { salt: string; unit_id: string; bucket: number }[];
  assignment_spec: {
    key: string;
    salt: string;
    traffic_pct: number;
    variants: { key: string; allocation_pct: number }[];
  };
  assignment: { unit_id: string; variant_key: string }[];
}

const fixtures = JSON.parse(
  readFileSync(new URL("../../fixtures/bucketing.json", import.meta.url), "utf8"),
) as Fixtures;

describe("bucketing parity", () => {
  for (const c of fixtures.bucket) {
    it(`bucket(${JSON.stringify(c.salt)}, ${c.unit_id}) === ${c.bucket}`, () => {
      expect(bucket(c.salt, c.unit_id)).toBeCloseTo(c.bucket, 12);
    });
  }
});

describe("assignment parity", () => {
  const spec: ExperimentSpec = {
    key: fixtures.assignment_spec.key,
    salt: fixtures.assignment_spec.salt,
    trafficPct: fixtures.assignment_spec.traffic_pct,
    variants: fixtures.assignment_spec.variants.map((v) => ({
      key: v.key,
      allocationPct: v.allocation_pct,
    })),
  };

  for (const a of fixtures.assignment) {
    it(`assign ${a.unit_id} -> ${a.variant_key}`, () => {
      expect(assign(spec, a.unit_id).variantKey).toBe(a.variant_key);
    });
  }
});
