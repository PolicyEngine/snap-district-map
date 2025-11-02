# SNAP Benefits by Congressional District

![SNAP Benefits Map](snap_benefits_by_district.png)

## Overview

Survey-weighted estimates of total SNAP benefits by congressional district across all 50 states plus DC.

**Total SNAP Benefits: $69.4 billion**

## Prerequisites

```bash
uv pip install policyengine-us pandas --python ~/envs/pe/bin/python
```

## Running the Code

```bash
cd /home/baogorek/devl/code-snippets/calculation/snap
~/envs/pe/bin/python snap_districts.py
```

**Output:** `snap_by_congressional_district.csv`

## Data

- **Source:** PolicyEngine test repository (hf://policyengine/test) with corrected district assignments
- **Districts:** 436 congressional districts
- **Variables:** household_id, household_weight, congressional_district_geoid, state_fips, snap
- **Range:** $26M - $475M per district

## Results

### Top States by SNAP Benefits

| State FIPS | State | Total Benefits |
|------------|-------|----------------|
| 6          | CA    | $10.9B         |
| 36         | NY    | $5.5B          |
| 48         | TX    | $5.1B          |
| 12         | FL    | $4.3B          |
| 17         | IL    | $3.5B          |

### Top Districts by SNAP Benefits

| District | State FIPS | Total Benefits |
|----------|------------|----------------|
| 1502     | 15 (HI)    | $475M          |
| 3615     | 36 (NY)    | $463M          |
| 3613     | 36 (NY)    | $412M          |
| 621      | 6 (CA)     | $404M          |
| 1501     | 15 (HI)    | $403M          |

## Visualization

### Static Hexagonal Cartogram

Generate the static PNG visualization:

```bash
python3 plot_snap_hexmap.py
```

**Output:** `snap_benefits_by_district.png`

**Features:**
- Hexagonal cartogram (each hex = one congressional district)
- All 436 districts matched perfectly
- Orange-to-red color gradient
- Summary statistics printed to console

### Interactive Hexagonal Cartogram

**View the interactive map:**
```bash
python3 -m http.server 8000
# Open browser to http://localhost:8000/snap_hexmap_interactive.html
```

**Features:**
- PolicyEngine branding and color scheme
- Hexagonal cartogram layout (no geographic distortion)
- **Interactive hover** - shows state name, district, and SNAP benefits
- Statistics dashboard with total benefits ($69.4B), district count (436), and averages
- Zoom and pan enabled
- Clean white background (no basemap)

### React Component for PolicyEngine App

A production-ready React component is available in `SNAPDistrictMap.jsx`:

**Features:**
- **Interactive toggle** between hexagonal cartogram and geographic map views
- Hexagonal map (equal representation for each district)
- Geographic map (actual congressional district boundaries)
- Hover interactions showing district details and SNAP benefits
- Statistics dashboard
- Mobile-responsive design

**Integration steps:**
1. Copy `SNAPDistrictMap.jsx` to `/src/pages/policy/output/snap/`
2. Move data files to `/public/data/`:
   - `hex_congressional_districts.geojson` (608K)
   - `real_congressional_districts.geojson` (4.8M)
   - `snap_by_congressional_district.csv`
3. Add route in `PolicyEngine.jsx`
4. Update imports to match PolicyEngine app structure

**Dependencies:**
- `react-plotly.js` (already installed)
- `plotly.js` (already installed)

## Files

- `snap_districts.py` - Generate SNAP data by congressional district
- `snap_by_congressional_district.csv` - SNAP benefit data (436 districts)
- `plot_snap_hexmap.py` - Generate static hexagonal cartogram PNG
- `snap_hexmap_interactive.html` - Interactive hexagonal cartogram
- `convert_hex_to_geojson.py` - Convert hex shapefiles to GeoJSON
- `convert_census_to_geojson.py` - Convert Census Bureau shapefiles to GeoJSON
- `hex_congressional_districts.geojson` - Hexagonal cartogram GeoJSON (608K)
- `real_congressional_districts.geojson` - Geographic districts GeoJSON (4.8M, 118th Congress)
- `HexCDv31/` - Congressional district hex shapefile
- `HexDDv20/` - Non-voting delegate districts hex shapefile
- `cb_2023_us_cd118_5m.*` - Census Bureau 118th Congress shapefiles
- `SNAPDistrictMap.jsx` - React component for PolicyEngine app (with hex/real toggle)

## Data Sources

**Hexagonal cartogram:** [The Downballot's maps database](https://docs.google.com/spreadsheets/d/1LrBXlqrtSZwyYOkpEEXFwQggvtR0bHHTxs9kq4kjOjw/edit)

**Geographic boundaries:** [US Census Bureau Cartographic Boundary Files](https://www2.census.gov/geo/tiger/GENZ2023/shp/) - 118th Congressional Districts (2023)
