#!/usr/bin/env python3
"""
Create D3.js interactive choropleth map of UK mansion tax impact by constituency.

Generates standalone HTML files with toggle between geographic and hex views.
Matches the style of the UK Autumn Budget Dashboard.
"""

import json
import pandas as pd

# PolicyEngine styling - matching autumn budget dashboard
TEAL = "#319795"
TEAL_DARK = "#277674"


def simplify_geojson(input_path, output_path, keep_every=10):
    """Simplify GeoJSON by reducing polygon points (keep in British National Grid)."""
    print("Simplifying GeoJSON...")

    with open(input_path) as f:
        geojson = json.load(f)

    def simplify_coords(coords, keep_every):
        """Simplify by keeping every Nth point."""
        if isinstance(coords[0], (int, float)):
            return [round(coords[0], 0), round(coords[1], 0)]

        if len(coords) > 4:
            step = max(1, len(coords) // keep_every)
            coords = coords[::step]
            if coords[0] != coords[-1]:
                coords.append(coords[0])

        return [simplify_coords(c, keep_every) for c in coords]

    for feature in geojson['features']:
        geom = feature['geometry']
        geom['coordinates'] = simplify_coords(geom['coordinates'], keep_every)
        props = feature['properties']
        feature['properties'] = {
            'Name': props['Name'],
            'GSScode': props['GSScode'],
        }

    with open(output_path, 'w') as f:
        json.dump(geojson, f, separators=(',', ':'))

    import os
    size_kb = os.path.getsize(output_path) / 1024
    print(f"Saved simplified GeoJSON to {output_path} ({size_kb:.0f} KB)")
    return geojson


def load_hex_data():
    """Load hex coordinates from HexJSON."""
    print("Loading hex coordinates...")
    with open('data/uk-constituencies-2024.hexjson') as f:
        hexjson = json.load(f)

    hex_data = {}
    for gss_code, hex_info in hexjson['hexes'].items():
        hex_data[hex_info['n']] = {
            'q': hex_info['q'],
            'r': hex_info['r'],
            'gss': gss_code,
        }

    print(f"Loaded {len(hex_data)} hex coordinates")
    return hex_data


def load_mansion_tax_data(threshold='1m'):
    """Load mansion tax impact data."""
    df = pd.read_csv(f'constituency_impact_{threshold}.csv')
    return df


def create_d3_html(geojson, hex_data, impact_data, threshold='1m'):
    """Create standalone D3.js HTML map with geo/hex toggle."""
    print(f"Creating D3 HTML for £{threshold} threshold...")

    # Convert impact data to dict for JSON
    impact_dict = {}
    for _, row in impact_data.iterrows():
        impact_dict[row['constituency_name']] = {
            'pct': round(row['pct_households_affected'], 3),
            'num': int(row['num_sales']),
            'rev': int(row['estimated_annual_revenue']),
        }

    threshold_label = '£1.5m' if threshold == '1m' else '£2m'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mansion Tax Impact by Constituency ({threshold_label} threshold)</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Roboto', sans-serif;
            background: white;
        }}
        .map-wrapper {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 16px;
            max-width: 900px;
            margin: 0 auto;
        }}
        .map-header {{
            padding-bottom: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        .map-header h2 {{
            margin: 0 0 6px 0;
            color: #374151;
            font-size: 1rem;
            font-weight: 600;
        }}
        .map-header p {{
            margin: 0;
            color: #6b7280;
            font-size: 0.875rem;
        }}
        .map-top-bar {{
            display: flex;
            gap: 24px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .map-search-section {{
            flex: 1;
            min-width: 200px;
            max-width: 300px;
        }}
        .map-search-section h3 {{
            font-size: 0.875rem;
            font-weight: 600;
            color: #374151;
            margin: 0 0 8px 0;
        }}
        .search-container {{
            position: relative;
        }}
        .constituency-search {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 0.875rem;
            font-family: 'Roboto', sans-serif;
        }}
        .constituency-search:focus {{
            outline: none;
            border-color: {TEAL};
            box-shadow: 0 0 0 3px rgba(49, 151, 149, 0.1);
        }}
        .search-results {{
            position: absolute;
            z-index: 100;
            width: 100%;
            margin-top: 4px;
            background: white;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-height: 200px;
            overflow-y: auto;
            display: none;
        }}
        .search-result-item {{
            width: 100%;
            text-align: left;
            padding: 10px 12px;
            background: none;
            border: none;
            border-bottom: 1px solid #f3f4f6;
            cursor: pointer;
            font-family: 'Roboto', sans-serif;
        }}
        .search-result-item:last-child {{
            border-bottom: none;
        }}
        .search-result-item:hover {{
            background: #f9fafb;
        }}
        .result-name {{
            font-weight: 500;
            font-size: 0.875rem;
            color: #374151;
        }}
        .result-value {{
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 2px;
        }}
        .view-toggle {{
            display: flex;
            gap: 4px;
            background: #f3f4f6;
            padding: 4px;
            border-radius: 8px;
        }}
        .view-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Roboto', sans-serif;
            background: transparent;
            color: #6b7280;
        }}
        .view-btn:hover {{
            color: {TEAL};
        }}
        .view-btn.active {{
            background: white;
            color: {TEAL};
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .map-legend {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-left: auto;
        }}
        .legend-gradient {{
            width: 180px;
            height: 12px;
            border-radius: 3px;
            background: linear-gradient(to right, #e0e7ed, #7eb3d3, #2c6496, #1a4a6e);
        }}
        .legend-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #6b7280;
            width: 180px;
        }}
        .map-canvas {{
            position: relative;
            width: 100%;
            display: flex;
            justify-content: center;
        }}
        .map-canvas svg {{
            background: #ffffff;
            border-radius: 6px;
            width: 100%;
            height: auto;
            max-width: 800px;
        }}
        .constituency-path {{
            cursor: pointer;
            transition: opacity 0.1s ease;
        }}
        .constituency-path:hover {{
            opacity: 0.8;
        }}
        .hex {{
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .hex:hover {{
            opacity: 0.8;
        }}
        .map-controls {{
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            gap: 4px;
            background: white;
            padding: 4px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .zoom-btn {{
            width: 28px;
            height: 28px;
            background: transparent;
            border: none;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #6b7280;
            font-size: 18px;
            font-weight: bold;
        }}
        .zoom-btn:hover {{
            background: #f3f4f6;
            color: {TEAL};
        }}
        .tooltip {{
            position: absolute;
            background: white;
            border: 2px solid {TEAL};
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            pointer-events: none;
            min-width: 200px;
            transform: translate(-50%, -100%);
            margin-top: -10px;
            z-index: 100;
            display: none;
        }}
        .tooltip h4 {{
            font-size: 0.9rem;
            font-weight: 600;
            color: #374151;
            margin: 0 0 8px 0;
        }}
        .tooltip-value {{
            font-size: 1.25rem;
            font-weight: 700;
            color: {TEAL};
            margin: 4px 0;
        }}
        .tooltip-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #6b7280;
            margin: 4px 0;
        }}
        .source {{
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="map-wrapper">
        <div class="map-header">
            <h2>Mansion tax impact by constituency ({threshold_label} threshold)</h2>
            <p>Number of properties affected in each UK parliamentary constituency</p>
        </div>

        <div class="map-top-bar">
            <div class="map-search-section">
                <h3>Search constituency</h3>
                <div class="search-container">
                    <input type="text" class="constituency-search" placeholder="Type to search..." id="search-input">
                    <div class="search-results" id="search-results"></div>
                </div>
            </div>

            <div class="view-toggle">
                <button class="view-btn active" id="btn-geo">Geographic</button>
                <button class="view-btn" id="btn-hex">Hex</button>
            </div>

            <div class="map-legend">
                <div class="legend-gradient"></div>
                <div class="legend-labels">
                    <span>Lower %</span>
                    <span>Higher %</span>
                </div>
            </div>
        </div>

        <div class="map-canvas">
            <svg id="map" viewBox="-100 -50 1000 1000" preserveAspectRatio="xMidYMid meet"></svg>
            <div class="map-controls">
                <button class="zoom-btn" id="zoom-in" title="Zoom in">+</button>
                <button class="zoom-btn" id="zoom-out" title="Zoom out">−</button>
                <button class="zoom-btn" id="zoom-reset" title="Reset">↺</button>
            </div>
            <div class="tooltip" id="tooltip"></div>
        </div>

        <div class="source">
            Source: PolicyEngine analysis of Land Registry data (uprated to 2026-27 using OBR HPI)
        </div>
    </div>

    <script>
        const geoData = {json.dumps(geojson)};
        const hexData = {json.dumps(hex_data)};
        const impactData = {json.dumps(impact_dict)};

        const width = 800;
        const height = 900;
        const svg = d3.select('#map');
        const g = svg.append('g');
        const tooltip = document.getElementById('tooltip');

        let currentView = 'geo';

        // Calculate bounds of British National Grid coordinates
        let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
        geoData.features.forEach(feature => {{
            const traverse = (coords) => {{
                if (typeof coords[0] === 'number') {{
                    xMin = Math.min(xMin, coords[0]);
                    xMax = Math.max(xMax, coords[0]);
                    yMin = Math.min(yMin, coords[1]);
                    yMax = Math.max(yMax, coords[1]);
                }} else {{
                    coords.forEach(traverse);
                }}
            }};
            traverse(feature.geometry.coordinates);
        }});

        // Create scale to fit British National Grid into SVG
        const padding = 40;
        const dataWidth = xMax - xMin;
        const dataHeight = yMax - yMin;
        const geoScale = Math.min((width - 2 * padding) / dataWidth, (height - 2 * padding) / dataHeight);
        const geoOffsetX = (width - dataWidth * geoScale) / 2;
        const geoOffsetY = (height - dataHeight * geoScale) / 2;

        const projection = d3.geoTransform({{
            point: function(x, y) {{
                this.stream.point(
                    (x - xMin) * geoScale + geoOffsetX,
                    height - ((y - yMin) * geoScale + geoOffsetY)
                );
            }}
        }});

        const path = d3.geoPath().projection(projection);

        // Calculate hex bounds
        let hexQMin = Infinity, hexQMax = -Infinity, hexRMin = Infinity, hexRMax = -Infinity;
        Object.values(hexData).forEach(h => {{
            hexQMin = Math.min(hexQMin, h.q);
            hexQMax = Math.max(hexQMax, h.q);
            hexRMin = Math.min(hexRMin, h.r);
            hexRMax = Math.max(hexRMax, h.r);
        }});

        // Hex positioning
        const hexSize = 12;
        const hexWidth = hexSize * 2;
        const hexHeight = Math.sqrt(3) * hexSize;
        const hexRangeQ = hexQMax - hexQMin;
        const hexRangeR = hexRMax - hexRMin;
        const hexTotalWidth = hexRangeQ * hexWidth * 0.75 + hexWidth;
        const hexTotalHeight = hexRangeR * hexHeight + hexHeight;
        const hexOffsetX = (width - hexTotalWidth) / 2;
        const hexOffsetY = (height - hexTotalHeight) / 2;

        function getHexPosition(q, r) {{
            const x = hexOffsetX + (q - hexQMin) * hexWidth * 0.75 + hexWidth / 2;
            // Flip y-axis so south (London) is at the bottom
            const y = hexOffsetY + (hexRMax - r) * hexHeight + (q % 2 !== 0 ? hexHeight / 2 : 0) + hexHeight / 2;
            return {{ x, y }};
        }}

        // Hex path generator
        function hexPath(cx, cy, size) {{
            const angles = [0, 60, 120, 180, 240, 300].map(a => a * Math.PI / 180);
            const points = angles.map(a => [
                cx + size * Math.cos(a),
                cy + size * Math.sin(a)
            ]);
            return 'M' + points.map(p => p.join(',')).join('L') + 'Z';
        }}

        // Color scale - sequential teal based on % of constituency
        const maxPct = Math.max(...Object.values(impactData).map(d => d.pct));
        const colorScale = d3.scaleSequential()
            .domain([0, maxPct])
            .interpolator(t => d3.interpolate('#e0e7ed', '#1a4a6e')(Math.pow(t, 0.5)));

        // Calculate centroids for geo view
        const centroids = {{}};
        geoData.features.forEach(feature => {{
            const bounds = path.bounds(feature);
            centroids[feature.properties.Name] = {{
                x: (bounds[0][0] + bounds[1][0]) / 2,
                y: (bounds[0][1] + bounds[1][1]) / 2
            }};
        }});

        // Draw geographic view (initial)
        const paths = g.selectAll('path')
            .data(geoData.features)
            .join('path')
            .attr('d', path)
            .attr('class', 'constituency-path')
            .attr('fill', d => {{
                const data = impactData[d.properties.Name];
                return data ? colorScale(data.pct) : '#e0e7ed';
            }})
            .attr('stroke', '#fff')
            .attr('stroke-width', 0.3)
            .on('click', handleClick);

        function handleClick(event, d) {{
            event.stopPropagation();
            const name = d.properties ? d.properties.Name : d.name;
            const data = impactData[name] || {{ pct: 0, num: 0, rev: 0 }};
            showTooltip(name, data, event);
            // Highlight
            g.selectAll('.constituency-path, .hex')
                .attr('stroke', '#fff')
                .attr('stroke-width', currentView === 'geo' ? 0.3 : 1);
            d3.select(this)
                .attr('stroke', '{TEAL_DARK}')
                .attr('stroke-width', currentView === 'geo' ? 1.5 : 2);
        }}

        function showTooltip(name, data, event) {{
            tooltip.innerHTML = `
                <h4>${{name}}</h4>
                <div class="tooltip-row">
                    <span>Number</span>
                    <span>${{data.num.toLocaleString()}}</span>
                </div>
                <div class="tooltip-row">
                    <span>Percent</span>
                    <span>${{data.pct.toFixed(2)}}%</span>
                </div>
                <div class="tooltip-row">
                    <span>Est. revenue</span>
                    <span>£${{data.rev.toLocaleString()}}</span>
                </div>
            `;
            const rect = document.querySelector('.map-canvas').getBoundingClientRect();
            tooltip.style.left = (event.clientX - rect.left) + 'px';
            tooltip.style.top = (event.clientY - rect.top - 10) + 'px';
            tooltip.style.display = 'block';
        }}

        // Click outside to hide tooltip
        svg.on('click', () => {{
            tooltip.style.display = 'none';
            g.selectAll('.constituency-path, .hex')
                .attr('stroke', '#fff')
                .attr('stroke-width', currentView === 'geo' ? 0.3 : 1);
        }});

        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([1, 8])
            .on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }});
        svg.call(zoom);

        document.getElementById('zoom-in').onclick = () => svg.transition().call(zoom.scaleBy, 1.5);
        document.getElementById('zoom-out').onclick = () => svg.transition().call(zoom.scaleBy, 0.67);
        document.getElementById('zoom-reset').onclick = () => {{
            svg.transition().call(zoom.transform, d3.zoomIdentity);
            tooltip.style.display = 'none';
        }};

        // View toggle
        const btnGeo = document.getElementById('btn-geo');
        const btnHex = document.getElementById('btn-hex');

        btnGeo.onclick = () => {{
            if (currentView === 'geo') return;
            currentView = 'geo';
            btnGeo.classList.add('active');
            btnHex.classList.remove('active');
            switchToGeo();
        }};

        btnHex.onclick = () => {{
            if (currentView === 'hex') return;
            currentView = 'hex';
            btnHex.classList.add('active');
            btnGeo.classList.remove('active');
            switchToHex();
        }};

        function switchToHex() {{
            // Reset zoom
            svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
            tooltip.style.display = 'none';

            // Remove existing paths
            g.selectAll('path').remove();

            // Create hex data array
            const hexArray = geoData.features.map(feature => {{
                const name = feature.properties.Name;
                const hex = hexData[name];
                return {{
                    name: name,
                    hex: hex,
                    feature: feature
                }};
            }}).filter(d => d.hex);

            // Draw hexes
            g.selectAll('.hex')
                .data(hexArray)
                .join('path')
                .attr('class', 'hex')
                .attr('d', d => {{
                    const pos = getHexPosition(d.hex.q, d.hex.r);
                    return hexPath(pos.x, pos.y, hexSize);
                }})
                .attr('fill', d => {{
                    const data = impactData[d.name];
                    return data ? colorScale(data.pct) : '#e0e7ed';
                }})
                .attr('stroke', '#fff')
                .attr('stroke-width', 1)
                .style('opacity', 0)
                .on('click', function(event, d) {{
                    event.stopPropagation();
                    const data = impactData[d.name] || {{ pct: 0, num: 0, rev: 0 }};
                    showTooltip(d.name, data, event);
                    g.selectAll('.hex')
                        .attr('stroke', '#fff')
                        .attr('stroke-width', 1);
                    d3.select(this)
                        .attr('stroke', '{TEAL_DARK}')
                        .attr('stroke-width', 2);
                }})
                .transition()
                .duration(500)
                .style('opacity', 1);
        }}

        function switchToGeo() {{
            // Reset zoom
            svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
            tooltip.style.display = 'none';

            // Remove hexes
            g.selectAll('.hex').remove();

            // Redraw paths
            g.selectAll('path')
                .data(geoData.features)
                .join('path')
                .attr('d', path)
                .attr('class', 'constituency-path')
                .attr('fill', d => {{
                    const data = impactData[d.properties.Name];
                    return data ? colorScale(data.pct) : '#e0e7ed';
                }})
                .attr('stroke', '#fff')
                .attr('stroke-width', 0.3)
                .style('opacity', 0)
                .on('click', handleClick)
                .transition()
                .duration(500)
                .style('opacity', 1);
        }}

        // Search functionality
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        const allNames = geoData.features.map(f => f.properties.Name).sort();

        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value.toLowerCase();
            if (query.length < 2) {{
                searchResults.style.display = 'none';
                return;
            }}
            const matches = allNames
                .filter(name => name.toLowerCase().includes(query))
                .slice(0, 5);

            if (matches.length === 0) {{
                searchResults.style.display = 'none';
                return;
            }}

            searchResults.innerHTML = matches.map(name => {{
                const data = impactData[name] || {{ pct: 0, num: 0, rev: 0 }};
                return `
                    <button class="search-result-item" data-name="${{name}}">
                        <div class="result-name">${{name}}</div>
                        <div class="result-value">${{data.num.toLocaleString()}} · ${{data.pct.toFixed(2)}}%</div>
                    </button>
                `;
            }}).join('');
            searchResults.style.display = 'block';

            searchResults.querySelectorAll('.search-result-item').forEach(btn => {{
                btn.onclick = () => {{
                    const name = btn.dataset.name;
                    searchInput.value = name;
                    searchResults.style.display = 'none';

                    // Reset zoom first
                    svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);

                    // Show tooltip
                    const data = impactData[name] || {{ pct: 0, num: 0, rev: 0 }};
                    tooltip.innerHTML = `
                        <h4>${{name}}</h4>
                        <div class="tooltip-row"><span>Number</span><span>${{data.num.toLocaleString()}}</span></div>
                        <div class="tooltip-row"><span>Percent</span><span>${{data.pct.toFixed(2)}}%</span></div>
                        <div class="tooltip-row"><span>Est. revenue</span><span>£${{data.rev.toLocaleString()}}</span></div>
                    `;

                    if (currentView === 'geo') {{
                        // Highlight and zoom to constituency
                        g.selectAll('.constituency-path')
                            .attr('stroke', '#fff')
                            .attr('stroke-width', 0.3);
                        g.selectAll('.constituency-path')
                            .filter(d => d.properties.Name === name)
                            .attr('stroke', '{TEAL_DARK}')
                            .attr('stroke-width', 1.5);

                        const feature = geoData.features.find(f => f.properties.Name === name);
                        if (feature) {{
                            const bounds = path.bounds(feature);
                            const dx = bounds[1][0] - bounds[0][0];
                            const dy = bounds[1][1] - bounds[0][1];
                            const x = (bounds[0][0] + bounds[1][0]) / 2;
                            const y = (bounds[0][1] + bounds[1][1]) / 2;
                            const zoomScale = Math.min(4, 0.9 / Math.max(dx / width, dy / height));
                            const translate = [width / 2 - zoomScale * x, height / 2 - zoomScale * y];

                            svg.transition().duration(750).call(
                                zoom.transform,
                                d3.zoomIdentity.translate(translate[0], translate[1]).scale(zoomScale)
                            );

                            tooltip.style.left = '50%';
                            tooltip.style.top = '40%';
                            tooltip.style.display = 'block';
                        }}
                    }} else {{
                        // Highlight hex
                        g.selectAll('.hex')
                            .attr('stroke', '#fff')
                            .attr('stroke-width', 1);
                        g.selectAll('.hex')
                            .filter(d => d.name === name)
                            .attr('stroke', '{TEAL_DARK}')
                            .attr('stroke-width', 2);

                        const hex = hexData[name];
                        if (hex) {{
                            const pos = getHexPosition(hex.q, hex.r);
                            const zoomScale = 3;
                            const translate = [width / 2 - zoomScale * pos.x, height / 2 - zoomScale * pos.y];

                            svg.transition().duration(750).call(
                                zoom.transform,
                                d3.zoomIdentity.translate(translate[0], translate[1]).scale(zoomScale)
                            );

                            tooltip.style.left = '50%';
                            tooltip.style.top = '40%';
                            tooltip.style.display = 'block';
                        }}
                    }}
                }};
            }});
        }});

        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {{
            if (!e.target.closest('.search-container')) {{
                searchResults.style.display = 'none';
            }}
        }});
    </script>
</body>
</html>'''

    return html


def main():
    print("=" * 60)
    print("Creating D3.js Mansion Tax Maps with Geo/Hex Toggle")
    print("=" * 60)

    import os

    # Simplify GeoJSON (keep in British National Grid)
    geojson = simplify_geojson(
        'uk_constituencies_2024.geojson',
        'uk_constituencies_simple.geojson',
        keep_every=15
    )

    # Load hex data
    hex_data = load_hex_data()

    for threshold in ['1m', '2m']:
        print(f"\n--- {threshold} threshold ---")

        impact_data = load_mansion_tax_data(threshold)
        html = create_d3_html(geojson, hex_data, impact_data, threshold)

        html_path = f'mansion_tax_d3_{threshold}.html'
        with open(html_path, 'w') as f:
            f.write(html)

        html_size = os.path.getsize(html_path) / 1024
        print(f"✓ Saved {html_path} ({html_size:.0f} KB)")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
