import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatCards from "../components/StatCards";

describe("StatCards", () => {
  const stats = {
    totalBenefits: 69_400_000_000,
    totalPopulation: 42_000_000,
    districtCount: 436,
    avgPopulation: 96330,
  };

  it("renders all four stat cards", () => {
    render(<StatCards stats={stats} currentMetric="benefits" onMetricChange={() => {}} />);
    expect(screen.getByText("Total SNAP benefits")).toBeInTheDocument();
    expect(screen.getByText("SNAP recipients")).toBeInTheDocument();
    expect(screen.getByText("Congressional districts")).toBeInTheDocument();
    expect(screen.getByText("Avg recipients / district")).toBeInTheDocument();
  });

  it("formats total benefits in billions", () => {
    render(<StatCards stats={stats} currentMetric="benefits" onMetricChange={() => {}} />);
    expect(screen.getByText("$69.4B")).toBeInTheDocument();
  });

  it("formats population in millions", () => {
    render(<StatCards stats={stats} currentMetric="benefits" onMetricChange={() => {}} />);
    expect(screen.getByText("42.0M")).toBeInTheDocument();
  });

  it("shows district count as plain number", () => {
    render(<StatCards stats={stats} currentMetric="benefits" onMetricChange={() => {}} />);
    expect(screen.getByText("436")).toBeInTheDocument();
  });
});
