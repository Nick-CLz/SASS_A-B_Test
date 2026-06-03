import { bucket } from "./bucketing";
import type { Assignment, Attributes, ExperimentSpec, Targeting, VariantSpec } from "./types";

const MISSING = Symbol("missing");

function compare(actual: unknown, operator: string, value: unknown): boolean {
  if (operator === "exists") return actual !== MISSING;
  if (actual === MISSING) return false;
  switch (operator) {
    case "eq":
      return actual === value;
    case "ne":
      return actual !== value;
    case "in":
      return Array.isArray(value) && value.includes(actual);
    case "not_in":
      return Array.isArray(value) && !value.includes(actual);
    case "gt":
      return (actual as number) > (value as number);
    case "gte":
      return (actual as number) >= (value as number);
    case "lt":
      return (actual as number) < (value as number);
    case "lte":
      return (actual as number) <= (value as number);
    default:
      throw new Error(`unknown targeting operator: ${operator}`);
  }
}

export function evaluateTargeting(attributes: Attributes, targeting?: Targeting): boolean {
  const rules = targeting?.rules ?? [];
  if (rules.length === 0) return true;
  const results = rules.map((rule) => {
    const actual = rule.attribute in attributes ? attributes[rule.attribute] : MISSING;
    return compare(actual, rule.operator, rule.value);
  });
  return (targeting?.match ?? "all") === "all" ? results.every(Boolean) : results.some(Boolean);
}

function pickVariant(variants: VariantSpec[], point01: number): string | null {
  const total = variants.reduce((sum, v) => sum + v.allocationPct, 0);
  if (total <= 0) return null;
  const point = point01 * total;
  let cumulative = 0;
  for (const variant of variants) {
    cumulative += variant.allocationPct;
    if (point < cumulative) return variant.key;
  }
  return variants[variants.length - 1].key;
}

export function assign(
  spec: ExperimentSpec,
  unitId: string,
  attributes: Attributes = {},
): Assignment {
  const base = { experimentKey: spec.key };
  if (!evaluateTargeting(attributes, spec.targeting)) {
    return { ...base, eligible: false, inExperiment: false, variantKey: null, reason: "not_eligible" };
  }
  if (spec.layer) {
    const slot = bucket(spec.layer.salt, unitId);
    if (!(spec.layer.start <= slot && slot < spec.layer.end)) {
      return { ...base, eligible: true, inExperiment: false, variantKey: null, reason: "not_in_layer" };
    }
  } else if (bucket(`${spec.salt}:traffic`, unitId) >= (spec.trafficPct ?? 100) / 100) {
    return { ...base, eligible: true, inExperiment: false, variantKey: null, reason: "not_in_traffic" };
  }
  const variantKey = pickVariant(spec.variants, bucket(`${spec.salt}:variant`, unitId));
  if (variantKey === null) {
    return { ...base, eligible: true, inExperiment: false, variantKey: null, reason: "no_variants" };
  }
  return { ...base, eligible: true, inExperiment: true, variantKey, reason: "assigned" };
}
