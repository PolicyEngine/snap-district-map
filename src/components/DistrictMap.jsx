import React, { useState, useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import { scaleSequential } from "d3-scale";
import { getDistrictId, getDistrictLabel } from "../dataUtils";

const TEAL_COLORS = [
  "#E6FFFA",
  "#B2F5EA",
  "#81E6D9",
  "#4FD1C5",
  "#38B2AC",
  "#319795",
  "#2C7A7B",
  "#285E61",
  "#1D4044",
];

function tealInterpolator(t) {
  const index = Math.min(Math.floor(t * TEAL_COLORS.length), TEAL_COLORS.length - 1);
  return TEAL_COLORS[index];
}

export default function DistrictMap({
  geoJSON,
  snapData,
  mapType,
  metric,
  onDistrictClick,
}) {
  const [tooltip, setTooltip] = useState(null);

  const { colorScale, maxVal } = useMemo(() => {
    if (!geoJSON || !snapData) return { colorScale: () => "#ccc", maxVal: 0 };

    let max = 0;
    geoJSON.features.forEach((feature) => {
      const id = getDistrictId(feature, mapType);
      const info = snapData[id];
      if (!info) return;
      const val =
        metric === "benefits" ? info.benefits : info.population / 1e3;
      if (val > max) max = val;
    });

    const scale = scaleSequential().domain([0, max]).interpolator(tealInterpolator);
    return { colorScale: scale, maxVal: max };
  }, [geoJSON, snapData, mapType, metric]);

  if (!geoJSON || !snapData) {
    return <div style={{ textAlign: "center", padding: "40px" }}>Loading...</div>;
  }

  const mapConfig =
    mapType === "hex"
      ? {
          projection: "geoMercator",
          projectionConfig: { scale: 800, center: [-96, 38] },
          width: 900,
          height: 600,
        }
      : {
          projection: "geoAlbersUsa",
          projectionConfig: { scale: 1000 },
          width: 900,
          height: 600,
        };

  return (
    <div style={{ position: "relative" }}>
      <ComposableMap
        data-testid="composable-map"
        projection={mapConfig.projection}
        projectionConfig={mapConfig.projectionConfig}
        width={mapConfig.width}
        height={mapConfig.height}
        style={{ width: "100%", height: "auto" }}
      >
        <ZoomableGroup>
          <Geographies geography={geoJSON}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const id = getDistrictId(geo, mapType);
                const info = snapData[id];
                const val = info
                  ? metric === "benefits"
                    ? info.benefits
                    : info.population / 1e3
                  : 0;
                const fill = val > 0 ? colorScale(val) : "#f0f0f0";
                const label = getDistrictLabel(geo, mapType, info);

                return (
                  <Geography
                    key={geo.rsmKey || id}
                    geography={geo}
                    data-testid="geography"
                    data-geo-id={id}
                    fill={fill}
                    stroke="white"
                    strokeWidth={mapType === "hex" ? 1 : 0.5}
                    style={{
                      default: { outline: "none" },
                      hover: { outline: "none", fill: "#1D4044", cursor: "pointer" },
                      pressed: { outline: "none" },
                    }}
                    onMouseEnter={(e) => {
                      const rect = e.target.ownerSVGElement.getBoundingClientRect();
                      const clientX = e.clientX - rect.left;
                      const clientY = e.clientY - rect.top;
                      setTooltip({
                        x: clientX,
                        y: clientY,
                        label,
                        benefits: info?.benefits || 0,
                        population: info?.population || 0,
                      });
                    }}
                    onMouseLeave={() => setTooltip(null)}
                    onClick={() => {
                      if (info) onDistrictClick(id, label);
                    }}
                  />
                );
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      {tooltip && (
        <div
          style={{
            position: "absolute",
            left: tooltip.x + 10,
            top: tooltip.y - 60,
            background: "white",
            border: "1px solid #ddd",
            borderRadius: "8px",
            padding: "10px 14px",
            fontSize: "13px",
            fontFamily: "'Inter', sans-serif",
            boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
            pointerEvents: "none",
            zIndex: 100,
            maxWidth: "250px",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: "4px" }}>
            {tooltip.label}
          </div>
          <div>
            SNAP benefits: ${tooltip.benefits.toFixed(1)}M
          </div>
          <div>
            Recipients: {(tooltip.population / 1e3).toFixed(1)}K
          </div>
        </div>
      )}

      <ColorLegend maxVal={maxVal} metric={metric} />
    </div>
  );
}

function ColorLegend({ maxVal, metric }) {
  const label = metric === "benefits" ? "SNAP benefits ($M)" : "Recipients (thousands)";
  const gradientStops = TEAL_COLORS.map(
    (color, i) => `${color} ${(i / (TEAL_COLORS.length - 1)) * 100}%`
  ).join(", ");

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "10px",
        marginTop: "10px",
        fontFamily: "'Inter', sans-serif",
        fontSize: "12px",
        color: "#344054",
      }}
    >
      <span>0</span>
      <div
        style={{
          width: "200px",
          height: "12px",
          borderRadius: "6px",
          background: `linear-gradient(to right, ${gradientStops})`,
        }}
      />
      <span>{maxVal.toFixed(0)}</span>
      <span style={{ marginLeft: "4px", fontWeight: 500 }}>{label}</span>
    </div>
  );
}
