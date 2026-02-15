import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import MapToggle from "../components/MapToggle";

describe("MapToggle", () => {
  it("renders both toggle buttons", () => {
    render(<MapToggle mapType="hex" onToggle={() => {}} />);
    expect(screen.getByText("Hexagonal map")).toBeInTheDocument();
    expect(screen.getByText("Geographic map")).toBeInTheDocument();
  });

  it("calls onToggle with 'real' when geographic button clicked", () => {
    const onToggle = vi.fn();
    render(<MapToggle mapType="hex" onToggle={onToggle} />);
    fireEvent.click(screen.getByText("Geographic map"));
    expect(onToggle).toHaveBeenCalledWith("real");
  });

  it("calls onToggle with 'hex' when hexagonal button clicked", () => {
    const onToggle = vi.fn();
    render(<MapToggle mapType="real" onToggle={onToggle} />);
    fireEvent.click(screen.getByText("Hexagonal map"));
    expect(onToggle).toHaveBeenCalledWith("hex");
  });
});
