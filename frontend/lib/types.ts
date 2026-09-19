// API response types mirroring the Mallard /v1 API (docs/06-api-and-sdk.md).

export interface Variant {
  id: string;
  key: string;
  name: string;
  is_control: boolean;
  allocation_pct: number;
  payload: Record<string, unknown>;
}

export interface ExperimentMetricLink {
  id: string;
  metric_id: string;
  role: string;
  is_oec: boolean;
}

export interface Experiment {
  id: string;
  key: string;
  name: string;
  description: string;
  hypothesis: string;
  status: string;
  randomization_unit: string;
  layer_id: string | null;
  salt: string;
  decision: string | null;
  start_at: string | null;
  end_at: string | null;
  variants: Variant[];
  metrics: ExperimentMetricLink[];
}

export interface MetricResult {
  metric_key: string;
  variant_key: string;
  is_control: boolean;
  n: number;
  estimate: number | null;
  abs_effect: number | null;
  rel_effect: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  p_value: number | null;
  prob_to_beat_control: number | null;
  expected_loss: number | null;
  is_significant: boolean;
  method_detail: Record<string, unknown>;
}

export interface Srm {
  chi_square: number;
  p_value: number;
  is_mismatch: boolean;
  observed: Record<string, number>;
  expected: Record<string, number>;
}

export interface AnalysisRun {
  id: string;
  computed_at: string;
  status: string;
  method: Record<string, unknown>;
  srm: Srm | null;
  results: MetricResult[];
}
