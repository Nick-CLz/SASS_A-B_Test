import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExperimentTable } from "@/components/experiment-table";
import type { Experiment } from "@/lib/types";

const EXP: Experiment = {
  id: "1",
  key: "checkout",
  name: "Checkout",
  description: "",
  hypothesis: "",
  status: "running",
  randomization_unit: "user_id",
  layer_id: null,
  salt: "checkout",
  decision: null,
  start_at: null,
  end_at: null,
  variants: [
    { id: "a", key: "control", name: "", is_control: true, allocation_pct: 50, payload: {} },
    { id: "b", key: "t", name: "", is_control: false, allocation_pct: 50, payload: {} },
  ],
  metrics: [{ id: "m", metric_id: "x", role: "primary", is_oec: true }],
};

describe("ExperimentTable", () => {
  it("renders a row linking to the experiment detail", () => {
    render(<ExperimentTable experiments={[EXP]} />);
    const link = screen.getByRole("link", { name: "checkout" });
    expect(link).toHaveAttribute("href", "/experiments/checkout");
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("shows an empty state", () => {
    render(<ExperimentTable experiments={[]} />);
    expect(screen.getByText("No experiments yet.")).toBeInTheDocument();
  });
});
