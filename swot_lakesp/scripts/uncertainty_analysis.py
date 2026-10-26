#!/usr/bin/env python3
"""
uncertainty_analysis.py (LakeSP)
--------------------------------
Cross-examines declared SWOT LakeSP uncertainty metrics (wse_u, wse_std, area_tot_u)
against actual validation errors observed relative to in situ gauge observations.

Key metrics evaluated (following Chingaza System thesis & paper Table 4):
- Actual error: e_wse = wse_swot - wse_obs, e_area = area_swot - area_obs
- Standardized anomaly: |e| / uncertainty (how many times actual error exceeds declared)
- Percentage of observations falling within the declared ±uncertainty band
- Summary statistics: MAE, RMSE, Bias, and maximum absolute error.

Outputs:
    - lakesp_{reservoir}_uncertainty_comparison.csv (per-pass actual error vs declared uncertainty)
    - lakesp_{reservoir}_uncertainty_summary.csv (consolidated executive summary table)
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np


def merge_with_in_situ(df_swot, obs_csv):
    """Merges SWOT observations with in situ daily observations by date."""
    df_obs = pd.read_csv(obs_csv)
    
    # Standardize in situ dates (DD/MM/YYYY to YYYY-MM-DD)
    if "fecha" in df_obs.columns:
        df_obs["date"] = pd.to_datetime(df_obs["fecha"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    elif "date" in df_obs.columns:
        df_obs["date"] = pd.to_datetime(df_obs["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Rename obs columns to avoid collision
    rename_map = {}
    if "nivel" in df_obs.columns: rename_map["nivel"] = "wse_obs"
    if "area" in df_obs.columns: rename_map["area"] = "area_obs"
    if "volumen" in df_obs.columns: rename_map["volumen"] = "volumen_obs"
    df_obs = df_obs.rename(columns=rename_map)

    merged = pd.merge(df_swot, df_obs[["date", "wse_obs", "area_obs", "volumen_obs"]], on="date", how="inner")
    return merged


def run_uncertainty_analysis(input_csv, obs_csv, output_dir, reservoir):
    input_file = Path(input_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df_swot = pd.read_csv(input_file)
    merged = merge_with_in_situ(df_swot, obs_csv)

    if len(merged) == 0:
        print("Warning: No matching observation dates found between SWOT and in situ records.")
        return

    # Calculate actual errors
    merged["error_wse"] = merged["wse"] - merged["wse_obs"]
    merged["abs_error_wse"] = merged["error_wse"].abs()

    area_swot_col = "area_used" if "area_used" in merged.columns else ("area_detct" if "area_detct" in merged.columns else "area_total")
    merged["error_area"] = merged[area_swot_col] - merged["area_obs"]
    merged["abs_error_area"] = merged["error_area"].abs()

    # Standardized anomalies (actual error / declared uncertainty)
    merged["anomaly_wse_u"] = np.where(merged["wse_u"] > 0, merged["abs_error_wse"] / merged["wse_u"], np.nan)
    merged["anomaly_wse_std"] = np.where(merged["wse_std"] > 0, merged["abs_error_wse"] / merged["wse_std"], np.nan)
    
    area_u_col = "area_det_u" if "area_det_u" in merged.columns else "area_tot_u"
    if area_u_col in merged.columns:
        merged["anomaly_area_u"] = np.where(merged[area_u_col] > 0, merged["abs_error_area"] / merged[area_u_col], np.nan)

    # Check whether actual error is within declared uncertainty bands
    merged["within_wse_u_band"] = merged["abs_error_wse"] <= merged["wse_u"]
    merged["within_wse_std_band"] = merged["abs_error_wse"] <= merged["wse_std"]
    if area_u_col in merged.columns:
        merged["within_area_u_band"] = merged["abs_error_area"] <= merged[area_u_col]

    res_key = reservoir.lower().replace(" ", "_")
    detail_file = output_path / f"lakesp_{res_key}_uncertainty_comparison.csv"
    merged.to_csv(detail_file, index=False)
    print(f"Per-pass uncertainty comparison ({len(merged)} passes) saved to: {detail_file}")

    # Build summary metrics table (Table 4 in paper)
    n = len(merged)
    wse_u_mean = merged["wse_u"].mean()
    wse_max_err = merged["abs_error_wse"].max()
    wse_mae = merged["abs_error_wse"].mean()
    wse_within = merged["within_wse_u_band"].sum()
    wse_within_pct = (wse_within / n) * 100.0 if n > 0 else 0

    area_u_mean = merged[area_u_col].mean() if area_u_col in merged.columns else np.nan
    area_max_err = merged["abs_error_area"].max()
    area_mae = merged["abs_error_area"].mean()
    area_within = merged["within_area_u_band"].sum() if "within_area_u_band" in merged.columns else 0
    area_within_pct = (area_within / n) * 100.0 if n > 0 else 0

    summary_rows = [
        {
            "Variable": "WSE (m)",
            "Reservoir": reservoir,
            "N": n,
            "Declared_Uncertainty_Mean": round(wse_u_mean, 3),
            "Max_Actual_Error": round(wse_max_err, 3),
            "MAE": round(wse_mae, 3),
            "Error_Over_Uncertainty": f"{round(wse_max_err / wse_u_mean, 1)}x" if wse_u_mean > 0 else "N/A",
            "Within_Band_Count": f"{wse_within} / {n}",
            "Within_Band_Pct": f"{round(wse_within_pct, 1)}%"
        },
        {
            "Variable": "Area (km²)",
            "Reservoir": reservoir,
            "N": n,
            "Declared_Uncertainty_Mean": round(area_u_mean, 3) if not np.isnan(area_u_mean) else "N/A",
            "Max_Actual_Error": round(area_max_err, 3),
            "MAE": round(area_mae, 3),
            "Error_Over_Uncertainty": f"{round(area_max_err / area_u_mean, 1)}x" if (area_u_mean and area_u_mean > 0) else "N/A",
            "Within_Band_Count": f"{area_within} / {n}",
            "Within_Band_Pct": f"{round(area_within_pct, 1)}%"
        }
    ]

    df_summary = pd.DataFrame(summary_rows)
    summary_file = output_path / f"lakesp_{res_key}_uncertainty_summary.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"Uncertainty summary table saved to: {summary_file}")
    print("\n" + df_summary.to_string(index=False))

    return merged, df_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SWOT LakeSP declared uncertainty vs validation errors.")
    parser.add_argument("--input", required=True, help="Cleaned LakeSP CSV")
    parser.add_argument("--obs", required=True, help="In situ daily observations CSV")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Reservoir name")
    args = parser.parse_args()

    run_uncertainty_analysis(args.input, args.obs, args.output, args.reservoir)
