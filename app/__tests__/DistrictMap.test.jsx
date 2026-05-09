import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DistrictMap from "../components/DistrictMap";

// Mock react-simple-maps since it requires actual geography data
vi.mock("react-simple-maps", () => ({
  ComposableMap: ({ children, ...props }) => (
    <div data-testid="composable-map" {...props}>
      {children}
    </div>
  ),
  Geographies: ({ children, geography }) => {
    const geos = geography?.features || [];
    return <g data-testid="geographies">{children({ geographies: geos })}</g>;
  },
  Geography: (props) => (
    <path data-testid="geography" data-geo-id={props["data-geo-id"]} />
  ),
  ZoomableGroup: ({ children }) => (
    <g data-testid="zoomable-group">{children}</g>
  ),
}));

describe("DistrictMap", () => {
  const mockGeoJSON = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { cd_id: 101, STATEAB: "AL", STATENAME: "Alabama", CDLABEL: "1" },
        geometry: { type: "Polygon", coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] },
      },
    ],
  };

  const mockSnapData = {
    101: {
      geoid: 101,
      stateFips: 1,
      stateName: "Alabama",
      benefits: 271.8,
      population: 113742,
      pctUnder18: 16.4,
      pctOver65: 30.9,
      medianIncome: 22425,
      employmentRate: 43.1,
    },
  };

  it("renders the composable map", () => {
    render(
      <DistrictMap
        geoJSON={mockGeoJSON}
        snapData={mockSnapData}
        mapType="hex"
        metric="benefits"
        onDistrictClick={() => {}}
      />
    );
    expect(screen.getByTestId("composable-map")).toBeInTheDocument();
  });

  it("renders geography elements for each feature", () => {
    render(
      <DistrictMap
        geoJSON={mockGeoJSON}
        snapData={mockSnapData}
        mapType="hex"
        metric="benefits"
        onDistrictClick={() => {}}
      />
    );
    const geos = screen.getAllByTestId("geography");
    expect(geos).toHaveLength(1);
  });
});
