  ~/envs/pe/bin/python snap_districts.py
  This creates snap_by_congressional_district.csv with the raw data.

  2. View Interactive Hexagonal Map (recommended)

  python3 -m http.server 8000
  # Then open: http://localhost:8000/snap_hexmap_interactive.html
  This shows an interactive visualization where you can hover over districts to see SNAP benefits.

  3. Generate Static PNG Image

  python3 plot_snap_hexmap.py
  Creates snap_benefits_by_district.png - a hexagonal cartogram showing the data.

  4. React Component (for PolicyEngine integration)

  If you want to use this in a React app, there's SNAPDistrictMap.jsx - a production-ready component with hex/geographic map toggle.

