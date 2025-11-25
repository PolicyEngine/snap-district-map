#!/usr/bin/env python3
"""Download data for UK mansion tax analysis."""

import os
import json
import csv
import zipfile
import requests
from pathlib import Path

def download(url, dest, desc):
    """Download file with progress."""
    print(f"\n{desc}...")
    if os.path.exists(dest):
        print(f"  ✓ {dest} (already exists)")
        return True

    Path(dest).parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Download failed: {e}")
        return False

    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = (downloaded / total * 100) if total else 0
                print(f"\r  {downloaded/1024/1024:.1f} MB / {total/1024/1024:.1f} MB ({pct:.0f}%)", end='', flush=True)
    print(f"\n  ✓ {dest}")
    return True

def download_and_convert_constituencies():
    """Download constituency names from ArcGIS API and convert to CSV."""
    dest = "data/Westminster_Parliamentary_Constituency_names_and_codes_UK_as_at_12_24.csv"

    if os.path.exists(dest):
        print(f"\n✓ {dest} (already exists)")
        return True

    print(f"\nDownloading Westminster constituency names...")
    url = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Westminster_Parliamentary_Constituencies_July_2024_Boundaries_UK_BGC/FeatureServer/0/query?where=1%3D1&outFields=PCON24CD,PCON24NM&returnGeometry=false&outSR=4326&f=json"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['PCON24CD', 'PCON24NM'])
            for feature in data['features']:
                writer.writerow([
                    feature['attributes']['PCON24CD'],
                    feature['attributes']['PCON24NM']
                ])
        print(f"  ✓ {dest}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def extract_nspl_zip():
    """Extract NSPL zip file."""
    zip_path = "data/NSPL_FEB_2025.zip"
    extract_dir = "data/NSPL"

    if os.path.exists(extract_dir) and os.listdir(extract_dir):
        print(f"\n✓ {extract_dir}/ (already extracted)")
        return True

    if not os.path.exists(zip_path):
        print(f"\n✗ {zip_path} not found, cannot extract")
        return False

    print(f"\nExtracting {zip_path}...")
    Path(extract_dir).mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        members = [m for m in zip_ref.namelist()
                  if m.startswith('Data/multi_csv/') and m.endswith('.csv')]
        for member in members:
            filename = Path(member).name
            with zip_ref.open(member) as source:
                with open(f"{extract_dir}/{filename}", 'wb') as target:
                    target.write(source.read())

    print(f"  ✓ Extracted {len(members)} files to {extract_dir}/")
    return True

print("="*60)
print("Downloading data for UK Mansion Tax Analysis")
print("="*60)

success = True

# 1. Land Registry 2024 data
if not download(
    "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-2024.csv",
    "data/pp-2024.csv",
    "1. Land Registry 2024 data (122 MB)"
):
    success = False

# 2. NSPL Postcode Lookup
if not download(
    "https://www.arcgis.com/sharing/rest/content/items/5dd216d9899044348a5b08fee09ac5a4/data",
    "data/NSPL_FEB_2025.zip",
    "2. NSPL Postcode Lookup (192 MB)"
):
    success = False
else:
    extract_nspl_zip()

# 3. Census 2021 Household Data
if not download(
    "https://ukds-ckan.s3.eu-west-1.amazonaws.com/2021/ONS/release1/Household-Characteristics/Household-Composition/TS003-Household-Composition-2021-p19wpc-ONS.xlsx",
    "data/TS003_household_composition_p19wpc.xlsx",
    "3. Census 2021 Household Data (200 KB)"
):
    success = False

# 4. Westminster Constituency Names
if not download_and_convert_constituencies():
    success = False

print("\n" + "="*60)
if success:
    print("✓ All downloads complete!")
    print("\nNext step: python analyze.py")
else:
    print("⚠ Some downloads failed - check errors above")
print("="*60)
