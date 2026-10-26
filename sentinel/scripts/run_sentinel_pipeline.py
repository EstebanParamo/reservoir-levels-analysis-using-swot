#!/usr/bin/env python3
"""
run_sentinel_pipeline.py
------------------------
Master orchestrator for the Sentinel-2 MSI Water Delineation & Validation Pipeline.

Coordinates:
    1. compute_ndwi.py: Ingests Green (B03) and NIR (B08) and computes NDWI raster.
    2. extract_water_mask.py: Thresholds continuous index into binary water mask.
    3. polygonize_and_area.py: Converts mask to vector, reprojects to MAGNA-SIRGAS 2018 (EPSG:9377),
       and computes surface area (km²).
    4. validate_sentinel_area.py: Statistically validates the resulting time series against in situ data.

Usage:
    python scripts/run_sentinel_pipeline.py \
      --green "/path/to/B03.tif" \
      --nir "/path/to/B08.tif" \
      --boundary "/path/to/reservoir_boundary.gpkg" \
      --obs "/path/to/gauge_obs.csv" \
      --output "/path/to/results" \
      --reservoir "chuza" \
      --date "2024-03-15"
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(script_path, args):
    cmd = [sys.executable, str(script_path)] + args
    print(f"\n---> Running: {script_path.name}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error executing {script_path.name}. Pipeline aborted.")
        sys.exit(1)


def execute_sentinel_pipeline(green_band, nir_band, boundary, obs_csv,
                               output_dir, reservoir, date_str, pipeline_dir):
    pipeline_dir = Path(pipeline_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    res_key = reservoir.lower().replace(" ", "_")

    print("=================================================================")
    print(f" STARTING SENTINEL-2 PIPELINE: {reservoir.upper()} ({date_str})")
    print("=================================================================")

    # 1. Compute NDWI
    ndwi_file = output_dir / f"ndwi_{res_key}_{date_str}.tif"
    run_step(
        pipeline_dir / "compute_ndwi.py",
        ["--green", str(green_band), "--nir", str(nir_band), "--output", str(ndwi_file)]
    )

    # 2. Extract Water Mask
    mask_file = output_dir / f"water_mask_{res_key}_{date_str}.tif"
    run_step(
        pipeline_dir / "extract_water_mask.py",
        ["--ndwi", str(ndwi_file), "--output", str(mask_file), "--threshold", "0.0", "--filter"]
    )

    # 3. Polygonize and compute area
    vector_file = output_dir / f"water_contour_{res_key}_{date_str}.gpkg"
    time_series_csv = output_dir / f"sentinel_{res_key}_time_series.csv"
    poly_args = [
        "--mask", str(mask_file),
        "--output_vector", str(vector_file),
        "--output_csv", str(time_series_csv),
        "--date", date_str,
        "--reservoir", res_key
    ]
    if boundary:
        poly_args.extend(["--boundary", str(boundary)])
    run_step(pipeline_dir / "polygonize_and_area.py", poly_args)

    # 4. Validate if in situ observations provided
    if obs_csv and Path(obs_csv).exists():
        run_step(
            pipeline_dir / "validate_sentinel_area.py",
            ["--sentinel", str(time_series_csv), "--obs", str(obs_csv),
             "--output", str(output_dir), "--reservoir", res_key]
        )

    print("\n=================================================================")
    print(f" SENTINEL-2 PROCESSING COMPLETED FOR: {reservoir.upper()}")
    print("=================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master orchestrator for Sentinel-2 water pipeline.")
    parser.add_argument("--green", required=True, help="Band 3 (Green) path")
    parser.add_argument("--nir", required=True, help="Band 8 (NIR) path")
    parser.add_argument("--boundary", default=None, help="Reservoir boundary shapefile/GeoPackage")
    parser.add_argument("--obs", default=None, help="In situ daily observations CSV for validation")
    parser.add_argument("--output", required=True, help="Destination directory")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Target reservoir")
    parser.add_argument("--date", required=True, help="Acquisition date (YYYY-MM-DD)")
    parser.add_argument("--pipeline_dir", default=None, help="Pipeline scripts directory")

    args = parser.parse_args()
    pip_dir = Path(args.pipeline_dir) if args.pipeline_dir else Path(__file__).resolve().parent

    execute_sentinel_pipeline(
        args.green, args.nir, args.boundary, args.obs,
        args.output, args.reservoir, args.date, pip_dir
    )
