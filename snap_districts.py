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

    # Sanity checks
    #In [23]: np.sum(sim.calculate("income_tax", map_to="person").weights.values) / 1E6
    #Out[23]: np.float64(10.54938186125562)
    #
    #In [24]: np.sum(sim.calculate("income_tax", map_to="household").weights.values) / 1E6
    #Out[24]: np.float64(3.620385739208581)


    # Get household-level data including income
    household_df = sim.calculate_dataframe([
        "household_id", "household_weight", "congressional_district_geoid",
        "state_fips", "household_market_income", "snap"],
        map_to="household")

    # Get person-level data for counting people receiving SNAP with age and employment
    # NOTE: the snap amount will be repeated (broadcast) to all people in the household
    person_df = sim.calculate_dataframe([
        "person_id", "person_household_id", "age", "employment_income"],
        map_to="person")

    hh_snap_data = household_df[['household_id', 'snap']].rename(
        columns={'snap': 'hh_snap'}
    )

    person_df = person_df.merge(
        hh_snap_data,
        left_on='person_household_id',  # Key from person_df
        right_on='household_id',        # Key from hh_snap_data
        how='left'
    )

    person_df = person_df.drop(columns=['household_id'])

    ## We just really need all weights to be consistent with reality.
    ## You can't have the same weight and twice the people
    #sim = Microsimulation(dataset=f"hf://policyengine/policyengine-us-data/cps_2023.h5")
    #spm_df = sim.calculate_dataframe([
    #    "spm_unit_id",
    #    "snap"
    #    ],
    #map_to="spm_unit")

    #person_df = sim.calculate_dataframe([
    #    "person_id",
    #    "snap"
    #    ],
    #map_to="person")

    #snap_hh = person_df.groupby('person_household_id')['snap'].sum().reset_index()
    #snap_hh.columns = ['household_id', 'snap']

    #household_df = household_df.merge(snap_hh)
    # Have to be very careful here because household_df is already a microdf:
    #In [35]: type(household_df)
    #Out[35]: microdf.microdataframe.MicroDataFrame

    #household_df['weighted_snap'] = household_df['household_weight'] * household_df['snap']

    # Count people receiving SNAP (snap > 0)
    person_df['receiving_snap'] = (person_df['hh_snap'] > 0).astype(int)
    #person_df['weighted_snap_recipients'] = person_df['household_weight'] * person_df['receiving_snap']

    # Count SNAP recipients by age groups
    person_df['snap_under_18'] = ((person_df['hh_snap'] > 0) & (person_df['age'] < 18)).astype(int)
    person_df['snap_over_65'] = ((person_df['hh_snap'] > 0) & (person_df['age'] >= 65)).astype(int)
    #person_df['weighted_snap_under_18'] = person_df['household_weight'] * person_df['snap_under_18']
    #person_df['weighted_snap_over_65'] = person_df['household_weight'] * person_df['snap_over_65']

    # Count employed SNAP recipients (employment_income > 0)
    person_df['snap_employed'] = ((person_df['hh_snap'] > 0) & (person_df['employment_income'] > 0)).astype(int)
    person_df['one'] = 1.0  # debugging
    #person_df['weighted_snap_employed'] = person_df['household_weight'] * person_df['snap_employed']
    
    # Define the list of new columns you want to sum
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
    # NOTE: You can see that "sum_of_one" just sums to the number of household records. These are not weighted sums (and I don't really know why)

    # Merge the new household counts back into the original household_df
    household_df = household_df.merge(
        hh_counts_df,
        left_on='household_id',         # Key from household_df
        right_on='person_household_id', # Key from hh_counts_df
        how='left'                      # Keep all original households
    )
    household_df = household_df.drop(columns=['person_household_id'])

  
    # These are the columns you already created by aggregating from person_df
    # (Using the friendlier names from my last answer)
    unweighted_counts = [
        'n_snap_recipients',
        'n_snap_under_18',
        'n_snap_over_65',
        'n_snap_employed'
    ]

    # We will create new columns by prefixing 'weighted_'
    weighted_counts = [f'weighted_{col}' for col in unweighted_counts]

    # Create the new weighted columns in household_df
    for i in range(len(unweighted_counts)):
        unweighted_col = unweighted_counts[i]
        weighted_col = weighted_counts[i]
        household_df[weighted_col] = household_df[unweighted_col].values * household_df['household_weight'].values

    grouping_cols = ['congressional_district_geoid', 'state_fips']
    cols_to_sum = weighted_counts + ['household_weight']
    district_totals = household_df.groupby(grouping_cols)[cols_to_sum].sum().reset_index()

    np.sum(district_totals.household_weight) / 1E6  # manual spot check for NC is good

    #weighted_totals = household_df.groupby(['congressional_district_geoid', 'state_fips'])['one'].sum().reset_index()
    #weighted_totals.rename(columns={'weighted_snap': 'total_weighted_snap'}, inplace=True)

    # Aggregate person counts including age breakdowns and employment
    #person_totals = household_df.groupby(['congressional_district_geoid', 'state_fips']).agg({
    #    'one': 'sum',
    #    'n_snap_recipients': 'sum',
    #    'n_snap_under_18': 'sum',
    #    'n_snap_over_65': 'sum',
    #    'n_snap_employed': 'sum'
    #}).reset_index()

    district_totals.rename(columns={
        'weighted_n_snap_recipients': 'snap_population',
        'weighted_n_snap_under_18': 'snap_under_18',
        'weighted_n_snap_over_65': 'snap_over_65',
        'weighted_n_snap_employed': 'snap_employed'
    }, inplace=True)

    # Calculate median household income by district for SNAP recipients only
    # Filter to only households receiving SNAP
    snap_households = household_df[household_df['snap'] > 0]  # .copy()  - copy breaks microdf

    # Test if microdf weights are being used - 'one' column should sum to millions (population)
    snap_households['one'] = 1

    # TODO: this isn't working
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

    ## Calculate weighted average income for SNAP households
    #income_by_district = snap_households.groupby(['congressional_district_geoid', 'state_fips']).apply(
    #    lambda x: np.average(x['household_market_income'], weights=x['household_weight']) if len(x) > 0 else 0
    #).reset_index()
    #income_by_district.rename(columns={0: 'median_household_income'}, inplace=True)

    # Merge all together
    combined = district_totals.merge(by_district, on=['congressional_district_geoid', 'state_fips'], how='left')
    #combined = combined.merge(by_district, on=['congressional_district_geoid', 'state_fips'], how='left')
    all_results.append(combined)

combined_df = pd.concat(all_results, ignore_index=True)

## What is this doing?
#combined_df = combined_df.groupby(['congressional_district_geoid', 'state_fips']).agg({
#    'total_weighted_snap': 'sum',
#    'snap_population': 'sum',
#    'snap_under_18': 'sum',
#    'snap_over_65': 'sum',
#    'snap_employed': 'sum',
#    'median_household_income': 'mean'
#}).reset_index()


snap_estimate = np.sum(combined_df.total_weighted_snap)
snap_target = 106744001279.0  # For a manual raking-style calibration

adj_factor = snap_target / snap_estimate

# Not idempoentent, so watch out!
combined_df['total_weighted_snap'] = adj_factor * combined_df['total_weighted_snap']

# Calculate percentages
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
