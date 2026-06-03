import { describe, expect, it } from "vitest";

import { assertNoPii, assertPseudonymousUnit, PIIError } from "../src/privacy";

describe("privacy guard", () => {
  it("rejects an email-like unit id", () => {
    expect(() => assertPseudonymousUnit("a@b.com")).toThrow(PIIError);
  });

  it("rejects an empty unit id", () => {
    expect(() => assertPseudonymousUnit("")).toThrow(PIIError);
  });

  it("accepts a pseudonymous id", () => {
    expect(() => assertPseudonymousUnit("user-123")).not.toThrow();
  });

  it("rejects PII-looking property keys", () => {
    expect(() => assertNoPii({ email: "x" })).toThrow(PIIError);
    expect(() => assertNoPii({ name: "Bob" })).toThrow(PIIError);
  });

  it("rejects email-valued properties", () => {
    expect(() => assertNoPii({ contact: "a@b.com" })).toThrow(PIIError);
  });

  it("allows clean, typed properties", () => {
    expect(() => assertNoPii({ country: "US", sku_count: 3 })).not.toThrow();
  });
});
