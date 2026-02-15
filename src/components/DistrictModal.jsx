import React from "react";

export default function DistrictModal({ district, label, onClose }) {
  if (!district) return null;

  const annualPerCapita =
    district.population > 0
      ? (district.benefits * 1e6) / district.population
      : 0;
  const monthlyPerCapita = annualPerCapita / 12;

  const rows = [
    { label: "State", value: district.stateName },
    { label: "District", value: district.geoid },
    { label: "SNAP benefits (annual)", value: `$${district.benefits.toFixed(1)}M` },
    {
      label: "Recipients",
      value: `${(district.population / 1e3).toFixed(1)}K`,
    },
    {
      label: "Monthly SNAP per recipient",
      value: `$${monthlyPerCapita.toFixed(0)}`,
    },
    { label: "% recipients under 18", value: `${district.pctUnder18.toFixed(1)}%` },
    { label: "% recipients over 65", value: `${district.pctOver65.toFixed(1)}%` },
    {
      label: "Median household income",
      value: `$${district.medianIncome.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`,
    },
    { label: "Employment rate", value: `${district.employmentRate.toFixed(1)}%` },
  ];

  return (
    <div
      style={{
        position: "fixed",
        zIndex: 1000,
        left: 0,
        top: 0,
        width: "100%",
        height: "100%",
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "white",
          padding: "30px",
          borderRadius: "12px",
          width: "90%",
          maxWidth: "500px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
          fontFamily: "'Inter', sans-serif",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <div style={{ fontSize: "24px", fontWeight: 600, color: "#101828" }}>
            {label}
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              background: "none",
              border: "none",
              fontSize: "28px",
              cursor: "pointer",
              color: "#5A5A5A",
              lineHeight: "20px",
            }}
          >
            &times;
          </button>
        </div>
        <div style={{ marginTop: "20px" }}>
          {rows.map((row) => (
            <div
              key={row.label}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "15px 0",
                borderBottom: "1px solid #F2F4F7",
              }}
            >
              <div style={{ color: "#5A5A5A", fontWeight: 500 }}>{row.label}</div>
              <div style={{ color: "#101828", fontWeight: 700, fontSize: "18px" }}>
                {row.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
