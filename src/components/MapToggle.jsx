import React from "react";

const TEAL = "#319795";

export default function MapToggle({ mapType, onToggle }) {
  const buttonStyle = (active) => ({
    padding: "10px 24px",
    border: "none",
    borderRadius: "6px",
    background: active ? TEAL : "transparent",
    color: active ? "white" : "#333",
    fontWeight: active ? "bold" : "normal",
    cursor: "pointer",
    transition: "all 0.2s ease",
    fontSize: "14px",
    fontFamily: "'Inter', sans-serif",
  });

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        marginBottom: "20px",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          background: "#f0f0f0",
          borderRadius: "8px",
          padding: "4px",
        }}
      >
        <button style={buttonStyle(mapType === "hex")} onClick={() => onToggle("hex")}>
          Hexagonal map
        </button>
        <button style={buttonStyle(mapType === "real")} onClick={() => onToggle("real")}>
          Geographic map
        </button>
      </div>
    </div>
  );
}
