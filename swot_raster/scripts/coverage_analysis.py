# -------------------------------------------------------
# coverage_analysis.py
# Compute water surface coverage from SWOT water_area
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd
from pathlib import Path
import re
import argparse


def extract_date(filename):

    m = re.search(r"(\d{4}-\d{2}-\d{2})", filename)

    return m.group(1) if m else None


def compute_reservoir_area(shape_path):

    gdf = gpd.read_file(shape_path)

    # ensure projected CRS (meters)
    if gdf.crs is None:
        raise ValueError("Shapefile CRS undefined")

    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=32618)

    area_m2 = gdf.geometry.area.sum()

    return area_m2


def coverage_analysis(output_dir, shape_path):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped" / "area"

    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    # --------------------------------
    # reservoir area
    # --------------------------------

    reservoir_area = compute_reservoir_area(shape_path)

    print(f"\nReservoir area: {reservoir_area:.2f} m²\n")

    # --------------------------------
    # filter only water_area rasters
    # --------------------------------

    files = []

    for f in clipped_dir.glob("*.tif"):

        if re.match(r"^water_area_\d{4}-\d{2}-\d{2}\.tif$", f.name):
            files.append(f)

    files = sorted(files)

    print(f"Water area rasters detected: {len(files)}\n")

    rows = []

    for f in files:

        date = extract_date(f.name)

        with rasterio.open(f) as src:

            data = src.read(1).astype(float)

            if src.nodata is not None:
                data[data == src.nodata] = np.nan

        total_area = np.nansum(data)

        coverage = (total_area / reservoir_area) * 100

        row = {

            "date": date,

            "water_area_m2": float(total_area),

            "water_area_km2": float(total_area / 1e6),

            "reservoir_area_m2": float(reservoir_area),

            "reservoir_area_km2": float(reservoir_area / 1e6),

            "coverage_percent": float(coverage)

        }

        rows.append(row)

    df = pd.DataFrame(rows)

    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values("date")

    out_csv = csv_dir / "water_area_coverage.csv"

    df.to_csv(out_csv, index=False)

    print(f"\nCoverage statistics saved: {out_csv}\n")


# -------------------------------------------------------
# standalone execution
# -------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True,
        help="Results directory"
    )

    parser.add_argument(
        "--shape",
        required=True,
        help="Reservoir shapefile"
    )

    args = parser.parse_args()

    coverage_analysis(
        output_dir=args.output,
        shape_path=args.shape
    )