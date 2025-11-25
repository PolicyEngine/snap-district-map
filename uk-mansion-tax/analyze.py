#!/usr/bin/env python3
"""
UK Mansion Tax Analysis - 2024

Analyzes property sales above £1.5m and £2m thresholds by Westminster constituency.
Generates constituency-level statistics and household impact percentages.

Prices are uprated from 2024 transaction values to 2026-27 forecast values
using OBR house price index from October 2024 EFO.
"""

import pandas as pd
import glob
import sys
from pathlib import Path

# OBR House Price Index (Jan 2015 = 100)
# Source: OBR Economic and Fiscal Outlook, October 2024
# https://obr.uk/efo/economic-and-fiscal-outlook-october-2024/
OBR_HPI = {
    '2024': 148.743,        # Calendar year 2024
    '2025': 150.367,        # Calendar year 2025
    '2026': 153.098,        # Calendar year 2026
    '2026-27': 154.030,     # Financial year 2026-27
    '2027-28': 158.305,     # Financial year 2027-28
}

# Uprating factor: from 2024 to 2026-27
UPRATE_FROM = '2024'
UPRATE_TO = '2026-27'
UPRATE_FACTOR = OBR_HPI[UPRATE_TO] / OBR_HPI[UPRATE_FROM]


def check_file(path, description):
    """Check if required file exists."""
    if not Path(path).exists():
        print(f"ERROR: Missing {description}")
        print(f"  Expected: {path}")
        print("\nRun: python download_data.py")
        sys.exit(1)


def load_constituency_lookup():
    """Load constituency code to name mapping."""
    lookup_path = "data/Westminster_Parliamentary_Constituency_names_and_codes_UK_as_at_12_24.csv"
    check_file(lookup_path, "constituency names/codes")
    df = pd.read_csv(lookup_path)
    return dict(zip(df['PCON24CD'], df['PCON24NM']))


def load_postcode_mapping():
    """Load NSPL postcode to constituency mapping."""
    csv_files = glob.glob("data/NSPL/NSPL_FEB_2025_UK_*.csv")
    if not csv_files:
        print("ERROR: Missing NSPL postcode data")
        print("  Expected: data/NSPL/NSPL_FEB_2025_UK_*.csv")
        print("\nRun: python download_data.py")
        sys.exit(1)
    print(f"Loading {len(csv_files)} NSPL files...")
    dfs = [pd.read_csv(f, usecols=['pcds', 'pcon']) for f in csv_files]
    postcode_lookup = pd.concat(dfs, ignore_index=True)
    return postcode_lookup.dropna(subset=['pcon'])


def load_household_data():
    """Load Census 2021 household counts."""
    xlsx_path = 'data/TS003_household_composition_p19wpc.xlsx'
    check_file(xlsx_path, "Census 2021 household data")
    df = pd.read_excel(xlsx_path, sheet_name='Dataset')
    df = df[df['Household composition (15 categories)'] != 'Does not apply']
    households = df.groupby([
        'Post-2019 Westminster Parliamentary constituencies Code',
        'Post-2019 Westminster Parliamentary constituencies'
    ])['Observation'].sum().reset_index()
    households.columns = ['constituency_code', 'constituency_name', 'total_households']
    return households


def analyze_threshold(threshold, const_names, postcode_to_const, households):
    """Analyze properties above threshold by constituency."""
    threshold_label = f'{threshold//1_000_000}m'
    print(f"\nProcessing £{threshold:,} threshold...")
    print(f"  Uprating 2024 prices to {UPRATE_TO} (factor: {UPRATE_FACTOR:.4f})")

    # Load property data
    pp_path = 'data/pp-2024.csv'
    check_file(pp_path, "Land Registry 2024 data")
    print("Loading property data...")
    df = pd.read_csv(pp_path, header=None, names=[
        'transaction_id', 'price', 'date', 'postcode', 'property_type',
        'old_new', 'duration', 'paon', 'saon', 'street', 'locality',
        'town', 'district', 'county', 'ppd_category', 'record_status'
    ])

    # Uprate prices to forecast year using OBR HPI
    df['price_uprated'] = df['price'] * UPRATE_FACTOR

    # Filter based on uprated prices
    df = df[df['price_uprated'] >= threshold]
    print(f"  Properties above £{threshold:,} (uprated): {len(df):,}")

    # Match to constituencies
    df['pcds'] = df['postcode'].str.strip().str.upper()
    df = df.merge(postcode_to_const, on='pcds', how='left')
    df['constituency_name'] = df['pcon'].map(const_names)

    # Calculate constituency stats (using uprated prices)
    const_stats = df[df['pcon'].notna()].groupby('constituency_name').agg({
        'price_uprated': ['count', 'mean', 'median', 'sum']
    }).round(0)
    const_stats.columns = ['num_sales', 'mean_price', 'median_price', 'total_value']
    const_stats['estimated_annual_revenue'] = const_stats['num_sales'] * 2000
    const_stats = const_stats.sort_values('num_sales', ascending=False)

    # Add household percentages
    const_stats = const_stats.merge(households[['constituency_name', 'total_households']],
                                     left_index=True, right_on='constituency_name', how='left')
    const_stats['pct_households_affected'] = (
        const_stats['num_sales'] / const_stats['total_households'] * 100
    ).round(3)

    # Save constituency impact
    const_stats = const_stats.sort_values('num_sales', ascending=False)
    const_stats.to_csv(f'constituency_impact_{threshold_label}.csv', index=False)

    # Save household impact
    household_impact = const_stats[['constituency_name', 'pct_households_affected']].copy()
    household_impact['avg_loss_per_household'] = 2000
    household_impact = household_impact.sort_values('pct_households_affected', ascending=False)
    household_impact.to_csv(f'household_impact_{threshold_label}.csv', index=False)

    return const_stats


if __name__ == '__main__':
    print("="*60)
    print("UK Mansion Tax Analysis")
    print("="*60)
    print(f"\nOBR House Price Index uprating:")
    print(f"  From: {UPRATE_FROM} (HPI: {OBR_HPI[UPRATE_FROM]})")
    print(f"  To:   {UPRATE_TO} (HPI: {OBR_HPI[UPRATE_TO]})")
    print(f"  Factor: {UPRATE_FACTOR:.4f} (+{(UPRATE_FACTOR-1)*100:.2f}%)")

    print("\nLoading reference data...")
    const_names = load_constituency_lookup()
    postcode_to_const = load_postcode_mapping()
    households = load_household_data()

    stats_1_5m = analyze_threshold(1_500_000, const_names, postcode_to_const, households)
    print(f"  {len(stats_1_5m)} constituencies, {stats_1_5m['num_sales'].sum():.0f} sales")

    stats_2m = analyze_threshold(2_000_000, const_names, postcode_to_const, households)
    print(f"  {len(stats_2m)} constituencies, {stats_2m['num_sales'].sum():.0f} sales")

    print("\n" + "="*60)
    print("Generated:")
    print("  constituency_impact_1m.csv")
    print("  constituency_impact_2m.csv")
    print("  household_impact_1m.csv")
    print("  household_impact_2m.csv")
    print("="*60)
