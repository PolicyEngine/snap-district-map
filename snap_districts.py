import pandas as pd
import numpy as np

from policyengine_us import Microsimulation
from microdf import MicroDataFrame


states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
          'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
          'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
          'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
          'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']


def subset_microdf(mdf, condition):
    """Subset a MicroDataFrame while preserving weights.
    
    Args:
        mdf: MicroDataFrame to subset
        condition: Boolean array/Series for filtering
    
    Returns:
        MicroDataFrame with filtered rows and corresponding weights
    """
    # Filter the data - .loc[] returns plain DataFrame
    filtered_data = pd.DataFrame(mdf.loc[condition])

    # Filter the weights using boolean values
    filtered_weights = mdf.weights[condition.values]

    # Create new MicroDataFrame
    return mdf.__class__(filtered_data, weights=filtered_weights)


all_results = []

for state in states:
    print(f"Processing {state}...")
    sim = Microsimulation(dataset=f"hf://policyengine/policyengine-us-data/{state}.h5")

    household_df = sim.calculate_dataframe([
        "household_id", "household_weight", "congressional_district_geoid",
        "state_fips", "household_market_income", "snap"],
        map_to="household")

    person_df = sim.calculate_dataframe([
        "person_id", "person_household_id", "age", "employment_income"],
        map_to="person")

    hh_snap_data = household_df[['household_id', 'snap']].rename(
        columns={'snap': 'hh_snap'}
    )

    person_df = person_df.merge(
        hh_snap_data,
        left_on='person_household_id',
        right_on='household_id',
        how='left'
    )

    person_df = person_df.drop(columns=['household_id'])

    person_df['receiving_snap'] = (person_df['hh_snap'] > 0).astype(int)
    person_df['snap_under_18'] = ((person_df['hh_snap'] > 0) & (person_df['age'] < 18)).astype(int)
    person_df['snap_over_65'] = ((person_df['hh_snap'] > 0) & (person_df['age'] >= 65)).astype(int)
    person_df['snap_employed'] = ((person_df['hh_snap'] > 0) & (person_df['employment_income'] > 0)).astype(int)
    person_df['one'] = 1.0

    cols_to_sum = [
        'one',
        'receiving_snap',
        'snap_under_18',
        'snap_over_65',
        'snap_employed'
    ]
    
    hh_counts_df = person_df.groupby('person_household_id')[cols_to_sum].sum().reset_index()
    hh_counts_df = hh_counts_df.rename(columns={
        'one': 'sum_of_one',
        'receiving_snap': 'n_snap_recipients',
        'snap_under_18': 'n_snap_under_18',
        'snap_over_65': 'n_snap_over_65',
        'snap_employed': 'n_snap_employed'
    })

    household_df = household_df.merge(
        hh_counts_df,
        left_on='household_id',
        right_on='person_household_id',
        how='left'
    )
    household_df = household_df.drop(columns=['person_household_id'])

    unweighted_counts = [
        'n_snap_recipients',
        'n_snap_under_18',
        'n_snap_over_65',
        'n_snap_employed'
    ]

    weighted_counts = [f'weighted_{col}' for col in unweighted_counts]
    for i in range(len(unweighted_counts)):
        unweighted_col = unweighted_counts[i]
        weighted_col = weighted_counts[i]
        household_df[weighted_col] = household_df[unweighted_col].values * household_df['household_weight'].values

    grouping_cols = ['congressional_district_geoid', 'state_fips']
    cols_to_sum = weighted_counts + ['household_weight']
    district_totals = household_df.groupby(grouping_cols)[cols_to_sum].sum().reset_index()

    district_totals.rename(columns={
        'weighted_n_snap_recipients': 'snap_population',
        'weighted_n_snap_under_18': 'snap_under_18',
        'weighted_n_snap_over_65': 'snap_over_65',
        'weighted_n_snap_employed': 'snap_employed'
    }, inplace=True)

    snap_households = household_df[household_df['snap'] > 0]
    snap_households['one'] = 1

    by_district_dfs = []
    for cd_id in set(snap_households.congressional_district_geoid):
        by_district_dfs.append(
            pd.DataFrame({
                'congressional_district_geoid': cd_id,
                'state_fips': cd_id // 100,
                'median_household_income': subset_microdf(snap_households, snap_households.congressional_district_geoid == cd_id).household_market_income.median(),
                'total_weighted_snap': subset_microdf(snap_households, snap_households.congressional_district_geoid == cd_id).snap.sum(),
                'one_sum_test': subset_microdf(snap_households, snap_households.congressional_district_geoid == cd_id).one.sum(),
            }, index=[cd_id])
        )
    by_district = pd.concat(by_district_dfs)

    combined = district_totals.merge(by_district, on=['congressional_district_geoid', 'state_fips'], how='left')
    all_results.append(combined)

combined_df = pd.concat(all_results, ignore_index=True)

snap_estimate = np.sum(combined_df.total_weighted_snap)
snap_target = 106744001279.0

adj_factor = snap_target / snap_estimate

combined_df['total_weighted_snap'] = adj_factor * combined_df['total_weighted_snap']

combined_df['pct_under_18'] = (combined_df['snap_under_18'] / combined_df['snap_population'] * 100).round(1)
combined_df['pct_over_65'] = (combined_df['snap_over_65'] / combined_df['snap_population'] * 100).round(1)
combined_df['employment_rate'] = (combined_df['snap_employed'] / combined_df['snap_population'] * 100).round(1)

combined_df = combined_df.sort_values(['state_fips', 'congressional_district_geoid'])
combined_df.to_csv('snap_by_congressional_district.csv', index=False)
print("--- Weighted SNAP Totals by Congressional District (All States) ---")
print(combined_df.head(10))
print(f"\nTotal districts: {len(combined_df)}")
if 'one_sum_test' in combined_df.columns:
    print(f"Test: Total 'one' sum (should be millions if weighted): {combined_df['one_sum_test'].sum():,.0f}")
print(f"Total SNAP benefits: ${combined_df['total_weighted_snap'].sum():,.0f}")
print(f"Total SNAP recipients: {combined_df['snap_population'].sum():,.0f}")
print(f"Avg % under 18: {combined_df['pct_under_18'].mean():.1f}%")
print(f"Avg % over 65: {combined_df['pct_over_65'].mean():.1f}%")
print(f"Avg employment rate: {combined_df['employment_rate'].mean():.1f}%")
print(f"Avg median household income: ${combined_df['median_household_income'].mean():,.0f}")
print(f"\nDistricts with SNAP < $1000: {(combined_df['total_weighted_snap'] < 1000).sum()}")
