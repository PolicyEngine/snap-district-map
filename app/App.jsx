"use client";

import React, { useState, useEffect } from "react";
import { parseCSV, computeStats } from "./dataUtils";
import MapToggle from "./components/MapToggle";
import StatCards from "./components/StatCards";
import DistrictMap from "./components/DistrictMap";
import DistrictModal from "./components/DistrictModal";

const TEAL = "#319795";

export default function App() {
  const [hexGeoJSON, setHexGeoJSON] = useState(null);
  const [realGeoJSON, setRealGeoJSON] = useState(null);
  const [snapData, setSnapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapType, setMapType] = useState("hex");
  const [metric, setMetric] = useState("benefits");
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [selectedLabel, setSelectedLabel] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const [hexRes, realRes, csvRes] = await Promise.all([
          fetch(`/data/hex_congressional_districts.geojson`),
          fetch(`/data/real_congressional_districts.geojson`),
          fetch(`/data/snap_by_congressional_district.csv`),
        ]);

        const hexData = await hexRes.json();
        const realData = await realRes.json();
        const csvText = await csvRes.text();
        const parsed = parseCSV(csvText);

        setHexGeoJSON(hexData);
        setRealGeoJSON(realData);
        setSnapData(parsed);
        setLoading(false);
      } catch (err) {
        console.error("Error loading data:", err);
        setError(err.message);
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "80px 40px", fontFamily: "'Inter', sans-serif" }}>
        <div
          style={{
            border: "4px solid #F2F4F7",
            borderTop: `4px solid ${TEAL}`,
            borderRadius: "50%",
            width: "48px",
            height: "48px",
            animation: "spin 1s linear infinite",
            margin: "0 auto 20px",
          }}
        />
        Loading map data...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: "center", padding: "80px 40px", color: "#e74c3c", fontFamily: "'Inter', sans-serif" }}>
        Error loading map: {error}
      </div>
    );
  }

  const stats = computeStats(snapData);
  const geoJSON = mapType === "hex" ? hexGeoJSON : realGeoJSON;

  function handleDistrictClick(id, label) {
    setSelectedDistrict(snapData[id]);
    setSelectedLabel(label);
  }

  return (
    <div style={{ fontFamily: "'Inter', sans-serif" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "40px 20px" }}>
        <div
          style={{
            background: "white",
            padding: "30px",
            borderRadius: "10px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            marginBottom: "30px",
          }}
        >
          <h1 style={{ color: "#101828", fontSize: "32px", fontWeight: 600, marginBottom: "8px" }}>
            SNAP benefits by congressional district
          </h1>
          <p style={{ color: "#5A5A5A", fontSize: "16px", lineHeight: 1.5, margin: 0 }}>
            Interactive visualization showing survey-weighted estimates of total SNAP
            benefits across all 50 states plus DC, calculated using the PolicyEngine
            microsimulation model.
          </p>
        </div>

        <MapToggle mapType={mapType} onToggle={setMapType} />

        <StatCards stats={stats} currentMetric={metric} onMetricChange={setMetric} />

        <div
          style={{
            background: "white",
            padding: "30px",
            borderRadius: "10px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <div style={{ color: "#101828", fontSize: "20px", fontWeight: 600, marginBottom: "20px" }}>
            {mapType === "hex" ? "Hexagonal cartogram" : "Geographic map"}
          </div>
          <DistrictMap
            geoJSON={geoJSON}
            snapData={snapData}
            mapType={mapType}
            metric={metric}
            onDistrictClick={handleDistrictClick}
          />
        </div>
      </div>

      <div
        style={{
          textAlign: "center",
          padding: "40px 20px",
          color: "#5A5A5A",
          fontSize: "14px",
        }}
      >
        Data sources: PolicyEngine microsimulation model | Hexagonal cartogram
        from The Downballot | Geographic boundaries from US Census Bureau |{" "}
        <a
          href="https://policyengine.org"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: TEAL, textDecoration: "none" }}
        >
          policyengine.org
        </a>
      </div>

      <DistrictModal
        district={selectedDistrict}
        label={selectedLabel}
        onClose={() => setSelectedDistrict(null)}
      />
    </div>
  );
}
