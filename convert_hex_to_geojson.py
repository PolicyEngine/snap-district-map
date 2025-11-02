import geopandas as gpd
import pandas as pd
import json

# Load hex shapefiles
hex_gdf = gpd.read_file('HexCDv31/HexCDv31.shp')
dc_gdf = gpd.read_file('HexDDv20/HexDDv20.shp')

# Filter DC and add necessary columns
dc_gdf = dc_gdf[dc_gdf['GEOID'] == '1198'].copy()
dc_gdf['STATEAB'] = dc_gdf['ABBREV']
dc_gdf['STATENAME'] = dc_gdf['NAME']
dc_gdf['CDLABEL'] = dc_gdf['ABBREV']

# Combine
combined_gdf = pd.concat([hex_gdf, dc_gdf], ignore_index=True)

# Add cd_id for matching
combined_gdf['cd_id'] = combined_gdf['GEOID'].astype(int)

# Fix single-district state mappings
single_district_states = {
    200: 201,   # Alaska
    1000: 1001, # Delaware
    3800: 3801, # North Dakota
    4600: 4601, # South Dakota
    5000: 5001, # Vermont
    5600: 5601, # Wyoming
    1198: 1101  # DC
}
combined_gdf['cd_id'] = combined_gdf['cd_id'].replace(single_district_states)

# Convert to GeoJSON
combined_gdf.to_file('hex_congressional_districts.geojson', driver='GeoJSON')

print(f"Converted {len(combined_gdf)} districts to GeoJSON")
print("Saved as: hex_congressional_districts.geojson")
