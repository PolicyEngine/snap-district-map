import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Load the SNAP data from CSV
snap_df = pd.read_csv('snap_by_congressional_district.csv')

# Convert benefits to millions for easier visualization
snap_df['snap_millions'] = snap_df['total_weighted_snap'] / 1e6

# Load the hexagon shapefile for voting districts
hex_gdf = gpd.read_file('HexCDv31/HexCDv31.shp')
hex_gdf['cd_id'] = hex_gdf['GEOID'].astype(int)

# Load non-voting districts shapefile and extract only DC
nonvoting_gdf = gpd.read_file('HexDDv20/HexDDv20.shp')
# Filter for DC only (GEOID 1198)
dc_gdf = nonvoting_gdf[nonvoting_gdf['GEOID'] == '1198'].copy()
dc_gdf['cd_id'] = dc_gdf['GEOID'].astype(int)
# Add state abbreviation column to match main shapefile structure
dc_gdf['STATEAB'] = dc_gdf['ABBREV']
dc_gdf['STATENAME'] = dc_gdf['NAME']
dc_gdf['CDLABEL'] = dc_gdf['ABBREV']

# Combine voting districts with DC only
hex_gdf = pd.concat([hex_gdf, dc_gdf], ignore_index=True)

# Fix single-district state mappings (at-large districts)
single_district_states = {
    200: 201,   # Alaska
    1000: 1001, # Delaware
    3800: 3801, # North Dakota
    4600: 4601, # South Dakota
    5000: 5001, # Vermont
    5600: 5601, # Wyoming
    1198: 1101  # DC (from 1198 in shapefile to 1101 in PolicyEngine data)
}
hex_gdf['cd_id'] = hex_gdf['cd_id'].replace(single_district_states)

# Merge SNAP data with shapefile
merged_gdf = hex_gdf.merge(
    snap_df[['congressional_district_geoid', 'state_fips', 'snap_millions']],
    left_on='cd_id',
    right_on='congressional_district_geoid',
    how='left'
)

# Create the visualization
fig, ax = plt.subplots(1, 1, figsize=(20, 12))

# Plot: SNAP Benefits by District (in millions)
merged_gdf.plot(
    column='snap_millions',
    ax=ax,
    legend=True,
    cmap='YlOrRd',  # Yellow to Orange to Red
    edgecolor='black',
    linewidth=0.3,
    missing_kwds={'color': 'lightgray', 'label': 'No Data'},
    legend_kwds={
        'label': 'SNAP Benefits ($ Millions)',
        'orientation': 'horizontal',
        'shrink': 0.8,
        'pad': 0.05
    }
)

ax.set_title('SNAP Benefits by Congressional District',
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

plt.tight_layout()
plt.savefig('snap_benefits_by_district.png', dpi=300, bbox_inches='tight')
print("Map saved as snap_benefits_by_district.png")

# Print summary statistics
print("\n=== Summary Statistics ===")
print(f"Districts with SNAP data: {snap_df.shape[0]}")
print(f"Total districts in shapefile: {hex_gdf.shape[0]}")
print(f"Districts matched: {merged_gdf['snap_millions'].notna().sum()}")

# Total SNAP benefits
total_snap = snap_df['total_weighted_snap'].sum()
print(f"\nTotal SNAP Benefits: ${total_snap/1e9:.1f} billion")
print(f"Average per District: ${snap_df['total_weighted_snap'].mean()/1e6:.1f} million")
print(f"Range: ${snap_df['total_weighted_snap'].min()/1e6:.1f}M - ${snap_df['total_weighted_snap'].max()/1e6:.1f}M")

# Top 10 districts by SNAP benefits
print(f"\nTop 10 Districts by SNAP Benefits:")
top_10 = snap_df.nlargest(10, 'total_weighted_snap')[['congressional_district_geoid', 'state_fips', 'snap_millions']]
top_10_formatted = top_10.copy()
top_10_formatted['snap_millions'] = top_10_formatted['snap_millions'].apply(lambda x: f"${x:.1f}M")
print(top_10_formatted.to_string(index=False))

# Bottom 10 districts by SNAP benefits
print(f"\nBottom 10 Districts by SNAP Benefits:")
bottom_10 = snap_df.nsmallest(10, 'total_weighted_snap')[['congressional_district_geoid', 'state_fips', 'snap_millions']]
bottom_10_formatted = bottom_10.copy()
bottom_10_formatted['snap_millions'] = bottom_10_formatted['snap_millions'].apply(lambda x: f"${x:.1f}M")
print(bottom_10_formatted.to_string(index=False))

# State totals
state_totals = snap_df.groupby('state_fips').agg({
    'total_weighted_snap': 'sum'
}).reset_index()
state_totals['snap_billions'] = state_totals['total_weighted_snap'] / 1e9
state_totals = state_totals.sort_values('snap_billions', ascending=False)

print(f"\nTop 10 States by Total SNAP Benefits:")
# Map state FIPS to names
state_names = {
    1: 'Alabama', 2: 'Alaska', 4: 'Arizona', 5: 'Arkansas', 6: 'California',
    8: 'Colorado', 9: 'Connecticut', 10: 'Delaware', 11: 'DC', 12: 'Florida',
    13: 'Georgia', 15: 'Hawaii', 16: 'Idaho', 17: 'Illinois', 18: 'Indiana',
    19: 'Iowa', 20: 'Kansas', 21: 'Kentucky', 22: 'Louisiana', 23: 'Maine',
    24: 'Maryland', 25: 'Massachusetts', 26: 'Michigan', 27: 'Minnesota',
    28: 'Mississippi', 29: 'Missouri', 30: 'Montana', 31: 'Nebraska',
    32: 'Nevada', 33: 'New Hampshire', 34: 'New Jersey', 35: 'New Mexico',
    36: 'New York', 37: 'North Carolina', 38: 'North Dakota', 39: 'Ohio',
    40: 'Oklahoma', 41: 'Oregon', 42: 'Pennsylvania', 44: 'Rhode Island',
    45: 'South Carolina', 46: 'South Dakota', 47: 'Tennessee', 48: 'Texas',
    49: 'Utah', 50: 'Vermont', 51: 'Virginia', 53: 'Washington',
    54: 'West Virginia', 55: 'Wisconsin', 56: 'Wyoming'
}

top_states = state_totals.head(10).copy()
top_states['state_name'] = top_states['state_fips'].map(state_names).fillna('Unknown')
top_states['snap_billions'] = top_states['snap_billions'].apply(lambda x: f"${x:.1f}B")
print(top_states[['state_name', 'snap_billions']].to_string(index=False))

plt.show()
