import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SrmBanner } from "@/components/srm-banner";
import type { Srm } from "@/lib/types";

const MISMATCH: Srm = {
  chi_square: 1143.4,
  p_value: 1e-250,
  is_mismatch: true,
  observed: { control: 12391, treatment: 7609 },
  expected: { control: 10000, treatment: 10000 },
};

describe("SrmBanner", () => {
  it("renders a loud alert on mismatch", () => {
    render(<SrmBanner srm={MISMATCH} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Sample Ratio Mismatch");
  });

  it("renders nothing when SRM is ok", () => {
    const { container } = render(<SrmBanner srm={{ ...MISMATCH, is_mismatch: false }} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when there is no SRM", () => {
    const { container } = render(<SrmBanner srm={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
