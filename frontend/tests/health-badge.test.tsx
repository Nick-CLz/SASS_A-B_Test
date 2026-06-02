import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HealthBadge } from "@/components/health-badge";

describe("HealthBadge", () => {
  it("shows the healthy label when state is ok", () => {
    render(<HealthBadge state="ok" />);
    expect(screen.getByRole("status")).toHaveTextContent("API healthy");
  });

  it("shows the error label when state is error", () => {
    render(<HealthBadge state="error" />);
    expect(screen.getByText("API unreachable")).toBeInTheDocument();
  });
});
