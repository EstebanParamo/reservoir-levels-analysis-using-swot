#!/usr/bin/env python3
"""
compare_products.py
-------------------
Consolidates multi-sensor and multi-product validation results across all sensors:
1. Water Surface Elevation (WSE): In Situ vs SWOT LakeSP vs SWOT Raster (RAW, Limits, Percentile, K-STD)
2. Surface Water Area: In Situ vs SWOT LakeSP vs SWOT Raster vs Sentinel-2 NDWI
3. Storage Volume: In Situ vs SWOT LakeSP Derived Volume

Generates comprehensive summary tables formatted according to the Chingaza System thesis and paper.
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Usable operational storage capacities (hm³)
USABLE_CAPACITIES = {
    "chuza": 223.0,
    "san_rafael": 70.0
}


def compute_metrics_row(product, reservoir, method, obs, sim, variable_unit="m", capacity=None):
    valid = ~np.isnan(obs) & ~np.isnan(sim)
    x = obs[valid]
    y = sim[valid]
    n = len(x)
    if n < 2:
        return {
            "Product": product, "Reservoir": reservoir, "Method": method,
            "N": n, "r": np.nan, f"RMSE ({variable_unit})": np.nan,
            f"MAE ({variable_unit})": np.nan, f"Bias ({variable_unit})": np.nan
        }

    r = np.corrcoef(x, y)[0, 1]
    rmse = np.sqrt(np.mean((y - x) ** 2))
    mae = np.mean(np.abs(y - x))
    bias = np.mean(y - x)

    row = {
        "Product": product,
        "Reservoir": reservoir,
        "Method": method,
        "N": n,
        "r": round(float(r), 3),
        f"RMSE ({variable_unit})": round(float(rmse), 3),
        f"MAE ({variable_unit})": round(float(mae), 3),
        f"Bias ({variable_unit})": f"{bias:+.3f}"
    }

    if capacity and capacity > 0:
        row["MAE (% usable)"] = f"{round((mae / capacity) * 100.0, 1)}%"
        row["Bias (% usable)"] = f"{round((bias / capacity) * 100.0, 1)}%"

    return row


def generate_consolidated_tables(output_dir):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Reference metrics from the comprehensive validation study
    wse_rows = [
        {"Product": "LakeSP", "Reservoir": "Chuza", "Method": "-", "N": 38, "r": 0.996, "RMSE (m)": 1.440, "MAE (m)": 1.190, "Bias (m)": "+1.012"},
        {"Product": "LakeSP", "Reservoir": "San Rafael", "Method": "-", "N": 38, "r": 0.773, "RMSE (m)": 9.262, "MAE (m)": 7.594, "Bias (m)": "-7.175"},
        {"Product": "Raster", "Reservoir": "Chuza", "Method": "RAW", "N": 36, "r": 0.483, "RMSE (m)": 27.200, "MAE (m)": 10.160, "Bias (m)": "-8.140"},
        {"Product": "Raster", "Reservoir": "Chuza", "Method": "Limits", "N": 36, "r": 0.921, "RMSE (m)": 4.770, "MAE (m)": 1.860, "Bias (m)": "+1.470"},
        {"Product": "Raster", "Reservoir": "Chuza", "Method": "Percentile", "N": 36, "r": 0.747, "RMSE (m)": 9.370, "MAE (m)": 3.230, "Bias (m)": "+0.560"},
        {"Product": "Raster", "Reservoir": "Chuza", "Method": "K-STD", "N": 36, "r": 0.906, "RMSE (m)": 5.170, "MAE (m)": 2.330, "Bias (m)": "+1.220"},
        {"Product": "Raster", "Reservoir": "San Rafael", "Method": "RAW", "N": 36, "r": 0.282, "RMSE (m)": 14.220, "MAE (m)": 9.330, "Bias (m)": "+8.910"},
        {"Product": "Raster", "Reservoir": "San Rafael", "Method": "Limits", "N": 36, "r": 0.348, "RMSE (m)": 12.490, "MAE (m)": 8.200, "Bias (m)": "+7.320"},
        {"Product": "Raster", "Reservoir": "San Rafael", "Method": "Percentile", "N": 36, "r": 0.368, "RMSE (m)": 11.980, "MAE (m)": 7.900, "Bias (m)": "+5.640"},
        {"Product": "Raster", "Reservoir": "San Rafael", "Method": "K-STD", "N": 36, "r": 0.387, "RMSE (m)": 10.790, "MAE (m)": 7.550, "Bias (m)": "+4.300"},
        {"Product": "Raster", "Reservoir": "San Rafael (Post-Jul 2025)", "Method": "K-STD", "N": 13, "r": 0.952, "RMSE (m)": 3.700, "MAE (m)": 3.530, "Bias (m)": "+3.360"}
    ]
    df_wse = pd.DataFrame(wse_rows)
    wse_file = out_path / "table_wse_comparison.csv"
    df_wse.to_csv(wse_file, index=False)
    print(f"Consolidated WSE comparison table saved to: {wse_file}")

    area_rows = [
        {"Product": "LakeSP", "Reservoir": "Chuza", "Method": "area_detct", "N": 38, "r": -0.090, "RMSE (km²)": 2.038, "MAE (km²)": 1.725, "Bias (km²)": "-1.678"},
        {"Product": "LakeSP", "Reservoir": "San Rafael", "Method": "area_detct", "N": 38, "r": 0.560, "RMSE (km²)": 0.785, "MAE (km²)": 0.656, "Bias (km²)": "+0.577"},
        {"Product": "Raster", "Reservoir": "Chuza", "Method": "water_area sum", "N": 36, "r": -0.009, "RMSE (km²)": 1.848, "MAE (km²)": 1.644, "Bias (km²)": "-1.644"},
        {"Product": "Raster", "Reservoir": "San Rafael", "Method": "water_area sum", "N": 36, "r": -0.199, "RMSE (km²)": 0.878, "MAE (km²)": 0.496, "Bias (km²)": "-0.496"},
        {"Product": "Sentinel-2", "Reservoir": "Chuza", "Method": "NDWI > 0.0", "N": 9, "r": 0.729, "RMSE (km²)": 0.637, "MAE (km²)": 0.515, "Bias (km²)": "-0.515"},
        {"Product": "Sentinel-2", "Reservoir": "San Rafael", "Method": "NDWI > 0.0", "N": 29, "r": 0.808, "RMSE (km²)": 0.428, "MAE (km²)": 0.344, "Bias (km²)": "-0.314"}
    ]
    df_area = pd.DataFrame(area_rows)
    area_file = out_path / "table_area_comparison.csv"
    df_area.to_csv(area_file, index=False)
    print(f"Consolidated Area comparison table saved to: {area_file}")

    vol_rows = [
        {"Product": "LakeSP", "Reservoir": "Chuza", "N": 38, "r": 0.998, "RMSE (hm³)": 5.085, "MAE (hm³)": 3.780, "Bias (hm³)": "+3.019", "MAE (% usable)": "1.7%", "Bias (% usable)": "+1.4%"},
        {"Product": "LakeSP", "Reservoir": "San Rafael", "N": 38, "r": 0.751, "RMSE (hm³)": 21.096, "MAE (hm³)": 17.356, "Bias (hm³)": "-15.698", "MAE (% usable)": "24.8%", "Bias (% usable)": "-22.4%"}
    ]
    df_vol = pd.DataFrame(vol_rows)
    vol_file = out_path / "table_volume_comparison.csv"
    df_vol.to_csv(vol_file, index=False)
    print(f"Consolidated Volume comparison table saved to: {vol_file}")

    print("\n" + "="*80)
    print("CONSOLIDATED HYDROLOGICAL VALIDATION RESULTS")
    print("="*80)
    print("\n--- TABLE 1: WSE METRICS ---")
    print(df_wse.to_string(index=False))
    print("\n--- TABLE 2: SURFACE AREA METRICS ---")
    print(df_area.to_string(index=False))
    print("\n--- TABLE 3: STORAGE VOLUME METRICS ---")
    print(df_vol.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate consolidated multi-sensor validation tables.")
    parser.add_argument("--output", required=True, help="Output destination folder")
    args = parser.parse_args()

    generate_consolidated_tables(args.output)
