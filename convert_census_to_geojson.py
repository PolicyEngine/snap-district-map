import geopandas as gpd
import json

# Load Census Bureau shapefile
census_gdf = gpd.read_file('cb_2023_us_cd118_5m.shp')

# Filter out territories - keep only 50 states + DC
# US states: FIPS codes 01-56 (with gaps)
# Territories to exclude: 60 (American Samoa), 66 (Guam), 69 (Northern Mariana Islands),
#                        72 (Puerto Rico), 78 (Virgin Islands)
territories = ['60', '66', '69', '72', '78']
census_gdf = census_gdf[~census_gdf['STATEFP'].isin(territories)]

# The Census shapefile has columns like STATEFP, CD118FP, GEOID, etc.
# We need to add columns to match the format expected by our React component

# Create STATE and CD columns for matching
census_gdf['STATE'] = census_gdf['STATEFP']
census_gdf['CD'] = census_gdf['CD118FP']

# The GEOID in Census data is already formatted as SSCDD (state + district)
# For example: "0601" for California's 1st district
census_gdf['GEOID_FULL'] = census_gdf['GEOID']

# Add a name field for hover text
census_gdf['NAME'] = census_gdf.apply(
    lambda row: f"{row['NAMELSAD']}",
    axis=1
)

# Convert to GeoJSON
census_gdf.to_file('real_congressional_districts.geojson', driver='GeoJSON')

print(f"Converted {len(census_gdf)} districts to GeoJSON")
print(f"Saved as: real_congressional_districts.geojson")

# Print some sample data to verify
print("\nSample districts:")
print(census_gdf[['STATEFP', 'CD118FP', 'GEOID', 'NAMELSAD']].head(10))
