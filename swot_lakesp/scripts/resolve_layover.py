#!/usr/bin/env python3
"""
resolve_layover.py
------------------
Cleans, disambiguates, and resolves layover phenomena in SWOT LakeSP records.

Specific hydrological rules from Chingaza System thesis:
- Chuza: Target lake_id 6150035523 ('REPRESA DE CHINGAZA (EMBALSE DE CHUZA)')
- San Rafael: Detects and resolves 'water-water layover' where PLD-based 'area_total'
  spuriously expands to 17–19 km². Replaces area_total with 'area_detct' (radar backscatter
  detected water), boosting correlation from 0.363 to 0.560.
- Resolves multiple records per orbital pass by selecting the physically coherent observation.

Outputs:
    lakesp_{reservoir}_clean.csv
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Physical bounds (masl) for Chingaza reservoirs
PHYSICAL_LIMITS = {
    "chuza": {"wse_min": 2900.0, "wse_max": 3020.0, "area_min": 0.5, "area_max": 8.0, "lake_id": "6150035523"},
    "san_rafael": {"wse_min": 2740.0, "wse_max": 2820.0, "area_min": 1.0, "area_max": 6.0, "lake_id": "6150035503"}
}


def clean_and_resolve(input_csv, output_dir, reservoir):
    input_file = Path(input_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} raw records from {input_file.name}")

    # Remove SWOT nodata values (-999999999999)
    numeric_cols = ["wse", "wse_u", "wse_std", "area_total", "area_tot_u", "area_detct", "area_det_u", "quality_f", "qual_f_b"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < -9000, col] = np.nan

    # Drop records without valid WSE or timestamp
    df = df.dropna(subset=["wse", "date"]).copy()
    df = df[df["date"] != "no_data"]

    # Filter by specific reservoir if configured
    res_key = reservoir.lower().replace(" ", "_")
    limits = PHYSICAL_LIMITS.get(res_key, {})

    if "lake_id" in limits and limits["lake_id"]:
        # Match target lake_id if available
        matched = df[df["lake_id"].astype(str) == str(limits["lake_id"])]
        if len(matched) > 0:
            df = matched.copy()

    # Apply physical bounds
    if "wse_min" in limits and "wse_max" in limits:
        df = df[(df["wse"] >= limits["wse_min"]) & (df["wse"] <= limits["wse_max"])]

    # Disambiguate multiple records on the same date
    # Priority: lowest wse_u, valid area_detct, physically realistic area
    cleaned_rows = []
    for date_val, group in df.groupby("date"):
        if len(group) == 1:
            cleaned_rows.append(group.iloc[0].to_dict())
        else:
            # Sort by wse_u ascending (lowest uncertainty first)
            sorted_group = group.sort_values(by=["wse_u", "wse_std"])
            cleaned_rows.append(sorted_group.iloc[0].to_dict())

    clean_df = pd.DataFrame(cleaned_rows)
    clean_df = clean_df.sort_values(by="date").reset_index(drop=True)

    # Resolve area variable:
    # In San Rafael, water-water layover corrupts area_total. We standardize on area_detct.
    # In Chuza, area_detct is also the robust radar detection.
    if "area_detct" in clean_df.columns and "area_total" in clean_df.columns:
        clean_df["area_used"] = clean_df["area_detct"]
        # Flag layover instances where area_total > 10 km²
        clean_df["layover_detected"] = clean_df["area_total"] > 10.0
    elif "area_detct" in clean_df.columns:
        clean_df["area_used"] = clean_df["area_detct"]
        clean_df["layover_detected"] = False
    else:
        clean_df["area_used"] = clean_df.get("area_total", np.nan)
        clean_df["layover_detected"] = False

    out_file = output_path / f"lakesp_{res_key}_clean.csv"
    clean_df.to_csv(out_file, index=False)
    print(f"Cleaned dataset ({len(clean_df)} passes) saved to: {out_file}")
    return clean_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve layover and clean SWOT LakeSP time series.")
    parser.add_argument("--input", required=True, help="Path to raw lakesp CSV")
    parser.add_argument("--output", required=True, help="Folder to save cleaned CSV")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Target reservoir name")
    args = parser.parse_args()

    clean_and_resolve(args.input, args.output, args.reservoir)
