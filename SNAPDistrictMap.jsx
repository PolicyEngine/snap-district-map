import React, { useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { formatCurrency } from "../../../lang/format"; // Adjust path as needed

/**
 * Interactive map showing SNAP benefits by congressional district
 *
 * This component displays a choropleth map of US congressional districts
 * colored by total SNAP benefits, with hover interactions showing details.
 */
export default function SNAPDistrictMap(props) {
  const { metadata, mobile } = props;
  const [hexGeoJSON, setHexGeoJSON] = useState(null);
  const [realGeoJSON, setRealGeoJSON] = useState(null);
  const [snapData, setSnapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapType, setMapType] = useState('hex'); // 'hex' or 'real'

  useEffect(() => {
    async function loadData() {
      try {
        // Load both GeoJSON files
        const hexResponse = await fetch('/data/hex_congressional_districts.geojson');
        const hexData = await hexResponse.json();

        const realResponse = await fetch('/data/real_congressional_districts.geojson');
        const realData = await realResponse.json();

        // Load SNAP data
        const snapResponse = await fetch('/data/snap_by_congressional_district.csv');
        const snapText = await snapResponse.text();

        // Parse CSV
        const lines = snapText.trim().split('\n');
        const snapDataMap = {};

        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',');
          const geoid = values[0];
          const stateFips = values[1].padStart(2, '0');
          const cd = geoid.slice(stateFips.length).padStart(2, '0');
          const fullGeoid = stateFips + cd;

          snapDataMap[fullGeoid] = {
            geoid: geoid,
            stateFips: stateFips,
            districtNumber: cd,
            totalSnap: parseFloat(values[2]),
            population: parseFloat(values[3])
          };
        }

        setHexGeoJSON(hexData);
        setRealGeoJSON(realData);
        setSnapData(snapDataMap);
        setLoading(false);
      } catch (err) {
        console.error('Error loading map data:', err);
        setError(err.message);
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px' }}>Loading map data...</div>;
  }

  if (error) {
    return <div style={{ textAlign: 'center', padding: '40px', color: '#e74c3c' }}>
      Error loading map: {error}
    </div>;
  }

  // Get current GeoJSON based on map type
  const geoJSON = mapType === 'hex' ? hexGeoJSON : realGeoJSON;

  // Calculate statistics
  const totalBenefits = Object.values(snapData).reduce((sum, d) => sum + d.totalSnap, 0);
  const totalPopulation = Object.values(snapData).reduce((sum, d) => sum + d.population, 0);
  const districtCount = Object.keys(snapData).length;
  const avgBenefits = totalBenefits / districtCount;
  const avgPopulation = totalPopulation / districtCount;

  // Prepare data for Plotly choropleth
  const locations = [];
  const z = [];
  const text = [];
  const customdata = [];

  geoJSON.features.forEach(feature => {
    // Handle both hex and real GeoJSON property names
    const state = (feature.properties.STATE || feature.properties.STATEFP).padStart(2, '0');
    const cd = (feature.properties.CD || feature.properties.CD118FP).padStart(2, '0');
    const locId = state + cd;

    const snapInfo = snapData[locId];
    const benefits = snapInfo ? snapInfo.totalSnap : 0;
    const population = snapInfo ? snapInfo.population : 0;

    locations.push(locId);
    z.push(benefits / 1e6); // Convert to millions for colorscale

    // Store district info for hover
    customdata.push({
      state: state,
      district: cd,
      benefits: benefits,
      population: population
    });

    // Build hover text
    const districtName = feature.properties.NAMELSAD
      ? feature.properties.NAMELSAD
      : feature.properties.NAME
      ? `District ${feature.properties.NAME}`
      : `District ${cd}`;

    text.push(
      `${districtName}<br>` +
      `State FIPS: ${state}<br>` +
      `SNAP Benefits: $${(benefits / 1e6).toFixed(1)}M<br>` +
      `Recipients: ${(population / 1e3).toFixed(1)}K`
    );
  });

  // Add location IDs to GeoJSON features for matching
  geoJSON.features.forEach((feature, idx) => {
    feature.id = locations[idx];
  });

  const data = [{
    type: 'choropleth',
    geojson: geoJSON,
    locations: locations,
    z: z,
    text: text,
    featureidkey: 'id',
    locationmode: 'geojson-id',
    colorscale: [
      [0, '#fee5d9'],
      [0.2, '#fcbba1'],
      [0.4, '#fc9272'],
      [0.6, '#fb6a4a'],
      [0.8, '#ef3b2c'],
      [1, '#a50f15']
    ],
    colorbar: {
      title: {
        text: 'SNAP Benefits<br>($M)',
        side: 'right'
      },
      thickness: 20,
      len: 0.7,
      outlinewidth: 0
    },
    hovertemplate: '%{text}<extra></extra>',
    marker: {
      line: {
        color: 'white',
        width: 0.5
      }
    }
  }];

  const layout = {
    geo: {
      scope: 'usa',
      projection: {
        type: 'albers usa'
      },
      showlakes: true,
      lakecolor: 'rgb(255, 255, 255)',
      bgcolor: 'rgba(0,0,0,0)'
    },
    height: mobile ? 500 : 700,
    margin: mobile
      ? { t: 0, b: 0, l: 0, r: 0 }
      : { t: 0, b: 0, l: 0, r: 0 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)'
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['select2d', 'lasso2d', 'pan2d', 'zoomIn2d', 'zoomOut2d'],
    displaylogo: false
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Map Type Toggle */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '20px'
      }}>
        <div style={{
          display: 'inline-flex',
          background: '#f0f0f0',
          borderRadius: '8px',
          padding: '4px'
        }}>
          <button
            onClick={() => setMapType('hex')}
            style={{
              padding: '10px 24px',
              border: 'none',
              borderRadius: '6px',
              background: mapType === 'hex' ? '#39C6C0' : 'transparent',
              color: mapType === 'hex' ? 'white' : '#333',
              fontWeight: mapType === 'hex' ? 'bold' : 'normal',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              fontSize: '14px'
            }}
          >
            Hexagonal Map
          </button>
          <button
            onClick={() => setMapType('real')}
            style={{
              padding: '10px 24px',
              border: 'none',
              borderRadius: '6px',
              background: mapType === 'real' ? '#39C6C0' : 'transparent',
              color: mapType === 'real' ? 'white' : '#333',
              fontWeight: mapType === 'real' ? 'bold' : 'normal',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              fontSize: '14px'
            }}
          >
            Geographic Map
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div style={{
        display: 'flex',
        gap: '20px',
        marginBottom: '30px',
        flexWrap: 'wrap'
      }}>
        <StatCard
          label="Total SNAP Benefits"
          value={`$${(totalBenefits / 1e9).toFixed(1)}B`}
        />
        <StatCard
          label="SNAP Recipients"
          value={`${(totalPopulation / 1e6).toFixed(1)}M`}
        />
        <StatCard
          label="Congressional Districts"
          value={districtCount}
        />
        <StatCard
          label="Avg Recipients / District"
          value={`${(avgPopulation / 1e3).toFixed(0)}K`}
        />
      </div>

      {/* Map */}
      <Plot
        data={data}
        layout={layout}
        config={config}
        style={{ width: '100%' }}
      />
    </div>
  );
}

/**
 * Statistics card component
 */
function StatCard({ label, value }) {
  return (
    <div style={{
      background: '#2C6496',
      color: 'white',
      padding: '20px',
      borderRadius: '8px',
      flex: '1',
      minWidth: '200px',
      transition: 'all 0.2s ease'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.background = '#1d3e5e';
      e.currentTarget.style.transform = 'translateY(-2px)';
      e.currentTarget.style.boxShadow = '0 4px 12px rgba(44, 100, 150, 0.25)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.background = '#2C6496';
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      <div style={{
        fontSize: '0.9em',
        opacity: 0.9,
        marginBottom: '5px'
      }}>
        {label}
      </div>
      <div style={{
        fontSize: '2em',
        fontWeight: 'bold'
      }}>
        {value}
      </div>
    </div>
  );
}
