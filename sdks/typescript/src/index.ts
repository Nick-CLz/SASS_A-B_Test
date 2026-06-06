// Mallard TypeScript SDK — deterministic assignment + privacy-guarded event tracking.

export { bucket } from "./bucketing";
export { assign, evaluateTargeting } from "./engine";
export { Mallard } from "./client";
export type { MallardOptions } from "./client";
export { PIIError, assertNoPii, assertPseudonymousUnit } from "./privacy";
export type {
  Assignment,
  Attributes,
  ExperimentSpec,
  LayerSlot,
  Targeting,
  TargetingRule,
  VariantSpec,
} from "./types";
