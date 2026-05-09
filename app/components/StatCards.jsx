import React from "react";

const TEAL = "#319795";
const TEAL_DARK = "#2C7A7B";

function StatCard({ label, value, clickable, active, onClick }) {
  const baseStyle = {
    background: TEAL,
    color: "white",
    padding: "24px",
    borderRadius: "10px",
    flex: "1",
    minWidth: "200px",
    transition: "all 0.2s ease",
    cursor: clickable ? "pointer" : "default",
    border: active ? "3px solid #E6FFFA" : "3px solid transparent",
    fontFamily: "'Inter', sans-serif",
  };

  return (
    <div
      style={baseStyle}
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = TEAL_DARK;
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow =
          "0 4px 12px rgba(49, 151, 149, 0.25)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = TEAL;
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div
        style={{
          fontSize: "14px",
          opacity: 0.9,
          marginBottom: "8px",
          textTransform: "uppercase",
          letterSpacing: "0.5px",
          fontWeight: 500,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: "36px", fontWeight: 700, lineHeight: 1 }}>
        {value}
      </div>
      {clickable && (
        <div style={{ fontSize: "11px", opacity: 0.7, marginTop: "5px" }}>
          Click to show on map
        </div>
      )}
    </div>
  );
}

export default function StatCards({ stats, currentMetric, onMetricChange }) {
  const { totalBenefits, totalPopulation, districtCount, avgPopulation } =
    stats;

  return (
    <div
      style={{
        display: "flex",
        gap: "20px",
        marginBottom: "30px",
        flexWrap: "wrap",
      }}
    >
      <StatCard
        label="Total SNAP benefits"
        value={`$${(totalBenefits / 1e9).toFixed(1)}B`}
        clickable
        active={currentMetric === "benefits"}
        onClick={() => onMetricChange("benefits")}
      />
      <StatCard
        label="SNAP recipients"
        value={`${(totalPopulation / 1e6).toFixed(1)}M`}
        clickable
        active={currentMetric === "recipients"}
        onClick={() => onMetricChange("recipients")}
      />
      <StatCard
        label="Congressional districts"
        value={districtCount}
      />
      <StatCard
        label="Avg recipients / district"
        value={`${(avgPopulation / 1e3).toFixed(0)}K`}
      />
    </div>
  );
}
