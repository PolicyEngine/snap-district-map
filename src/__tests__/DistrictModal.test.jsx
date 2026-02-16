import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import DistrictModal from "../components/DistrictModal";

describe("DistrictModal", () => {
  const district = {
    geoid: 101,
    stateName: "Alabama",
    benefits: 271.8,
    population: 113742,
    pctUnder18: 16.4,
    pctOver65: 30.9,
    medianIncome: 22425,
    employmentRate: 43.1,
  };

  it("renders nothing when district is null", () => {
    const { container } = render(
      <DistrictModal district={null} label="" onClose={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders district name when open", () => {
    render(
      <DistrictModal district={district} label="Alabama District 1" onClose={() => {}} />
    );
    expect(screen.getByText("Alabama District 1")).toBeInTheDocument();
  });

  it("shows SNAP benefits", () => {
    render(
      <DistrictModal district={district} label="Alabama District 1" onClose={() => {}} />
    );
    expect(screen.getByText("$271.8M")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = vi.fn();
    render(
      <DistrictModal district={district} label="Alabama District 1" onClose={onClose} />
    );
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalled();
  });
});
