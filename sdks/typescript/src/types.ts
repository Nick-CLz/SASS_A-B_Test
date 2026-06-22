export interface VariantSpec {
  key: string;
  allocationPct: number;
}

export interface LayerSlot {
  salt: string;
  start: number;
  end: number;
}

export interface TargetingRule {
  attribute: string;
  operator: string;
  value?: unknown;
}

export interface Targeting {
  match?: "all" | "any";
  rules?: TargetingRule[];
}

export interface ExperimentSpec {
  key: string;
  salt: string;
  variants: VariantSpec[];
  trafficPct?: number;
  targeting?: Targeting;
  layer?: LayerSlot | null;
}

export interface Assignment {
  experimentKey: string;
  eligible: boolean;
  inExperiment: boolean;
  variantKey: string | null;
  reason: string;
}

export type Attributes = Record<string, unknown>;
