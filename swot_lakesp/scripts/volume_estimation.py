#!/usr/bin/env python3
"""
volume_estimation.py
--------------------
Estimates reservoir storage volume (hm³) from SWOT water surface elevation (WSE)
using the official EAAB elevation-volume bathymetric rating curves (ENEL 2023 / EAAB 2024).

The rating curve interpolator is constructed from official reservoir gauge & bathymetric records.

Outputs:
    lakesp_{reservoir}_with_volume.csv
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np


def build_rating_curve(obs_csv):
    """Constructs interpolation functions for elevation-area and elevation-volume."""
    df_obs = pd.read_csv(obs_csv)
    # Parse levels, volume, area
    df_obs = df_obs.dropna(subset=["nivel", "volumen"]).copy()
    
    # Sort by water level ascending
    df_sorted = df_obs.sort_values(by="nivel").drop_duplicates(subset=["nivel"])
    levels = df_sorted["nivel"].values
    volumes = df_sorted["volumen"].values
    areas = df_sorted["area"].values if "area" in df_sorted.columns else None

    def level_to_volume(wse):
        return np.interp(wse, levels, volumes)

    def level_to_area(wse):
        if areas is not None:
            return np.interp(wse, levels, areas)
        return np.full_like(wse, np.nan)

    return level_to_volume, level_to_area


def estimate_volume(input_csv, obs_csv, output_dir, reservoir):
    input_file = Path(input_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df_swot = pd.read_csv(input_file)
    level_to_vol, level_to_area = build_rating_curve(obs_csv)

    # Estimate volume and reference area from SWOT WSE
    df_swot["volumen_swot_hm3"] = level_to_vol(df_swot["wse"].values)
    df_swot["area_ref_curva_km2"] = level_to_area(df_swot["wse"].values)

    res_key = reservoir.lower().replace(" ", "_")
    out_file = output_path / f"lakesp_{res_key}_with_volume.csv"
    df_swot.to_csv(out_file, index=False)
    print(f"Volume estimation completed. Saved to: {out_file}")
    return df_swot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate storage volume from SWOT WSE.")
    parser.add_argument("--input", required=True, help="Cleaned LakeSP CSV")
    parser.add_argument("--obs", required=True, help="Official in situ CSV with nivel, area, volumen")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Reservoir name")
    args = parser.parse_args()

    estimate_volume(args.input, args.obs, args.output, args.reservoir)
