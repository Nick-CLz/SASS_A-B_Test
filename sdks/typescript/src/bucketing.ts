import { createHash } from "node:crypto";

// 2**64 is exactly representable as a double, so dividing by it is an exact exponent
// shift — this is why Number(uint64) / 2**64 matches Python's uint64 / 2**64 bit-for-bit.
const TWO_POW_64 = 2 ** 64;

/**
 * Map (salt, unitId) deterministically into [0, 1).
 * Identical to the Python backend (see ../fixtures/bucketing.json).
 */
export function bucket(salt: string, unitId: string): number {
  const digest = createHash("sha256").update(`${salt}:${unitId}`, "utf8").digest();
  let value = 0n;
  for (let i = 0; i < 8; i++) {
    value = (value << 8n) | BigInt(digest[i]);
  }
  return Number(value) / TWO_POW_64;
}
