# UK Mansion Tax Analysis

Analysis of property sales above £1.5m and £2m by Westminster constituency using 2024 Land Registry data.

Based on [FT article (Nov 2025)](https://www.ft.com/content/8e375410-dde2-43bc-8cc3-c6ae37c1aef3): Labour considering council tax surcharge on high-value properties (bands F/G/H), estimated £600m annual revenue from 145k-300k homes.

## Quick Start

```bash
pip install -r requirements.txt
python download_data.py  # Auto-downloads all data (~340 MB)
python analyze.py        # Runs analysis, generates results
```

**That's it!** All data downloads automatically. Zero manual steps.

## Output Files

- `constituency_impact_1m.csv` - Sales, prices, revenue by constituency (£1.5m threshold)
- `constituency_impact_2m.csv` - Sales, prices, revenue by constituency (£2m threshold)
- `household_impact_1m.csv` - % of households affected (£1.5m threshold)
- `household_impact_2m.csv` - % of households affected (£2m threshold)

## Results Summary

**£1.5m threshold:** 14,581 sales (1.65% of 2024 transactions), 567 constituencies affected
**£2m threshold:** 8,328 sales (0.94% of 2024 transactions), 555 constituencies affected

Top constituency: Cities of London & Westminster (1.6% of households)

## Data Sources

- [UK Land Registry Price Paid Data 2024](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads) (147 MB)
- [ONS National Statistics Postcode Lookup](https://geoportal.statistics.gov.uk/) (192 MB)
- [Census 2021 TS003 Household Composition](https://statistics.ukdataservice.ac.uk/dataset/ons_2021_ts003_demography_household_composition) (200 KB)

## Note

This analysis uses 2024 **sales** data, not total housing stock. Actual policy impact would be ~10-20x larger (sales represent 5-10% of stock).
