import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResultsTable } from "@/components/results-table";
import type { MetricResult } from "@/lib/types";

const ROWS: MetricResult[] = [
  {
    metric_key: "conv",
    variant_key: "control",
    is_control: true,
    n: 1000,
    estimate: 0.1,
    abs_effect: null,
    rel_effect: null,
    ci_lower: null,
    ci_upper: null,
    p_value: null,
    prob_to_beat_control: null,
    expected_loss: null,
    is_significant: false,
    method_detail: {},
  },
  {
    metric_key: "conv",
    variant_key: "treatment",
    is_control: false,
    n: 1000,
    estimate: 0.14,
    abs_effect: 0.04,
    rel_effect: 0.4,
    ci_lower: 0.02,
    ci_upper: 0.06,
    p_value: 1e-5,
    prob_to_beat_control: 0.999,
    expected_loss: 0.0001,
    is_significant: true,
    method_detail: {},
  },
];

describe("ResultsTable", () => {
  it("shows the relative lift and a significant verdict", () => {
    render(<ResultsTable results={ROWS} />);
    expect(screen.getByText("+40.0%")).toBeInTheDocument();
    expect(screen.getByText("significant")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("marks the control row", () => {
    render(<ResultsTable results={ROWS} />);
    expect(screen.getByText("control")).toBeInTheDocument();
  });
});
