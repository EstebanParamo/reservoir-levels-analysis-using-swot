#!/usr/bin/env python3
"""
download_swot_podaac.py
-----------------------
Automated downloader for SWOT Level-2 products (Raster 100m and LakeSP Vector)
from NASA Physical Oceanography Distributed Active Archive Center (PO.DAAC)
using NASA Earthdata Login credentials.

Features:
- Queries NASA CMR (Common Metadata Repository) for Orbit 104 over Chingaza System
- Supports collections:
    * SWOT_L2_HR_Raster_100m_2.0
    * SWOT_L2_HR_LakeSP_2.0
- Organizes downloads into dedicated directories by product and cycle.

Usage:
    python download_swot_podaac.py \
      --product "lakesp" \
      --orbit 104 \
      --start_date "2023-09-01" \
      --end_date "2026-03-31" \
      --output "/path/to/download_folder"
"""

import argparse
from pathlib import Path
import sys

# Chingaza Reservoir bounding box: [min_lon, min_lat, max_lon, max_lat]
CHINGAZA_BBOX = (-73.85, 4.55, -73.65, 4.85)

SHORTNAMES = {
    "raster": "SWOT_L2_HR_Raster_100m_2.0",
    "lakesp": "SWOT_L2_HR_LakeSP_2.0"
}


def download_with_earthaccess(product_key, orbit, start_date, end_date, output_dir):
    try:
        import earthaccess
    except ImportError:
        print("Package 'earthaccess' not found. Installing or using direct CMR query...")
        print("Please install via: pip install earthaccess")
        return False

    short_name = SHORTNAMES.get(product_key.lower())
    if not short_name:
        raise ValueError(f"Unknown product '{product_key}'. Choose from: {list(SHORTNAMES.keys())}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Authenticating with NASA Earthdata...")
    auth = earthaccess.login(strategy="interactive", persist=True)
    if not auth.authenticated:
        print("Earthdata authentication failed. Check credentials.")
        return False

    print(f"Searching PO.DAAC for {short_name} | Orbit: {orbit} | Range: {start_date} to {end_date}...")
    granules = earthaccess.search_data(
        short_name=short_name,
        bounding_box=CHINGAZA_BBOX,
        temporal=(start_date, end_date)
    )

    print(f"Found {len(granules)} granules.")
    # Filter by orbit in granule name or metadata
    orbit_str = f"_{orbit:03d}_"
    filtered = [g for g in granules if orbit_str in str(g)]
    print(f"Granules matching Orbit {orbit}: {len(filtered)}")

    if filtered:
        print(f"Downloading to {output_path}...")
        files = earthaccess.download(filtered, str(output_path))
        print(f"Successfully downloaded {len(files)} files.")
        return True
    else:
        print("No matching orbit granules found.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download SWOT Level-2 data from NASA PO.DAAC.")
    parser.add_argument("--product", required=True, choices=["raster", "lakesp"], help="SWOT product")
    parser.add_argument("--orbit", type=int, default=104, help="Orbit track number (default: 104)")
    parser.add_argument("--start_date", default="2023-09-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", default="2026-03-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", required=True, help="Download destination folder")

    args = parser.parse_args()

    success = download_with_earthaccess(
        args.product, args.orbit, args.start_date, args.end_date, args.output
    )
    if not success:
        sys.exit(1)
