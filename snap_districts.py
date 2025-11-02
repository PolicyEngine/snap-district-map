import pandas as pd
import numpy as np
from policyengine_us import Microsimulation

states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
          'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
          'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
          'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
          'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

all_results = []

for state in states:
    print(f"Processing {state}...")
    sim = Microsimulation(dataset=f"hf://policyengine/policyengine-us-data/{state}.h5")
    print(f"  Using main repository for {state}")

    # Get household-level data including income
    household_df = sim.calculate_dataframe(["household_id", "household_weight", "congressional_district_geoid", "state_fips", "snap", "household_market_income"], map_to="household")
    household_df['weighted_snap'] = household_df['household_weight'] * household_df['snap']

    # Get person-level data for counting people receiving SNAP with age and employment
    person_df = sim.calculate_dataframe(["person_id", "person_household_id", "household_weight", "congressional_district_geoid", "state_fips", "snap", "age", "employment_income"], map_to="person")

    # Count people receiving SNAP (snap > 0)
    person_df['receiving_snap'] = (person_df['snap'] > 0).astype(int)
    person_df['weighted_snap_recipients'] = person_df['household_weight'] * person_df['receiving_snap']

    # Count SNAP recipients by age groups
    person_df['snap_under_18'] = ((person_df['snap'] > 0) & (person_df['age'] < 18)).astype(int)
    person_df['snap_over_65'] = ((person_df['snap'] > 0) & (person_df['age'] >= 65)).astype(int)
    person_df['weighted_snap_under_18'] = person_df['household_weight'] * person_df['snap_under_18']
    person_df['weighted_snap_over_65'] = person_df['household_weight'] * person_df['snap_over_65']

    # Count employed SNAP recipients (employment_income > 0)
    person_df['snap_employed'] = ((person_df['snap'] > 0) & (person_df['employment_income'] > 0)).astype(int)
    person_df['weighted_snap_employed'] = person_df['household_weight'] * person_df['snap_employed']

    # Aggregate household SNAP benefits
    weighted_totals = household_df.groupby(['congressional_district_geoid', 'state_fips'])['weighted_snap'].sum().reset_index()
    weighted_totals.rename(columns={'weighted_snap': 'total_weighted_snap'}, inplace=True)

    # Aggregate person counts including age breakdowns and employment
    person_totals = person_df.groupby(['congressional_district_geoid', 'state_fips']).agg({
        'weighted_snap_recipients': 'sum',
        'weighted_snap_under_18': 'sum',
        'weighted_snap_over_65': 'sum',
        'weighted_snap_employed': 'sum'
    }).reset_index()
    person_totals.rename(columns={
        'weighted_snap_recipients': 'snap_population',
        'weighted_snap_under_18': 'snap_under_18',
        'weighted_snap_over_65': 'snap_over_65',
        'weighted_snap_employed': 'snap_employed'
    }, inplace=True)

    # Calculate median household income by district for SNAP recipients only
    # Filter to only households receiving SNAP
    snap_households = household_df[household_df['snap'] > 0].copy()

    # Calculate weighted average income for SNAP households
    income_by_district = snap_households.groupby(['congressional_district_geoid', 'state_fips']).apply(
        lambda x: np.average(x['household_market_income'], weights=x['household_weight']) if len(x) > 0 else 0
    ).reset_index()
    income_by_district.rename(columns={0: 'median_household_income'}, inplace=True)

    # Merge all together
    combined = weighted_totals.merge(person_totals, on=['congressional_district_geoid', 'state_fips'], how='left')
    combined = combined.merge(income_by_district, on=['congressional_district_geoid', 'state_fips'], how='left')
    all_results.append(combined)

combined_df = pd.concat(all_results, ignore_index=True)
combined_df = combined_df.groupby(['congressional_district_geoid', 'state_fips']).agg({
    'total_weighted_snap': 'sum',
    'snap_population': 'sum',
    'snap_under_18': 'sum',
    'snap_over_65': 'sum',
    'snap_employed': 'sum',
    'median_household_income': 'mean'
}).reset_index()

# Calculate percentages
combined_df['pct_under_18'] = (combined_df['snap_under_18'] / combined_df['snap_population'] * 100).round(1)
combined_df['pct_over_65'] = (combined_df['snap_over_65'] / combined_df['snap_population'] * 100).round(1)
combined_df['employment_rate'] = (combined_df['snap_employed'] / combined_df['snap_population'] * 100).round(1)

combined_df = combined_df.sort_values(['state_fips', 'congressional_district_geoid'])
combined_df.to_csv('snap_by_congressional_district.csv', index=False)
print("--- Weighted SNAP Totals by Congressional District (All States) ---")
print(combined_df.head(10))
print(f"\nTotal districts: {len(combined_df)}")
print(f"Total SNAP benefits: ${combined_df['total_weighted_snap'].sum():,.0f}")
print(f"Total SNAP recipients: {combined_df['snap_population'].sum():,.0f}")
print(f"Avg % under 18: {combined_df['pct_under_18'].mean():.1f}%")
print(f"Avg % over 65: {combined_df['pct_over_65'].mean():.1f}%")
print(f"Avg employment rate: {combined_df['employment_rate'].mean():.1f}%")
print(f"Avg median household income: ${combined_df['median_household_income'].mean():,.0f}")
print(f"\nDistricts with SNAP < $1000: {(combined_df['total_weighted_snap'] < 1000).sum()}")
