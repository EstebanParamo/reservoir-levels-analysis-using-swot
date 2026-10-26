#!/usr/bin/env python3
"""
validate_sentinel_area.py
-------------------------
Validates Sentinel-2 derived surface water area time series against official in situ
reservoir observations (EAAB bathymetric rating curves applied to daily water levels).

Computes accuracy metrics:
- Pearson correlation coefficient (r)
- Root Mean Square Error (RMSE, km²)
- Mean Absolute Error (MAE, km²)
- Bias (Mean Error, km²)

Outputs:
    - sentinel_{reservoir}_validation_metrics.csv (Table 4-12 in thesis)
    - sentinel_{reservoir}_validation_plot.png (Figures 4-32 & 4-33 in thesis)
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})


def validate_sentinel(sentinel_csv, obs_csv, output_dir, reservoir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    res_key = reservoir.lower().replace(" ", "_")

    df_sentinel = pd.read_csv(sentinel_csv)
    if "reservoir" in df_sentinel.columns:
        df_sentinel = df_sentinel[df_sentinel["reservoir"].str.lower() == res_key].copy()

    df_obs = pd.read_csv(obs_csv)
    if "fecha" in df_obs.columns:
        df_obs["date"] = pd.to_datetime(df_obs["fecha"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")

    # Match dates
    merged = pd.merge(df_sentinel, df_obs[["date", "area"]], on="date", how="inner")
    merged = merged.rename(columns={"area": "area_obs", "area_km2": "area_sentinel"})

    n = len(merged)
    if n < 2:
        print(f"Insufficient matched dates ({n}) for statistical validation.")
        return

    x = merged["area_obs"].values
    y = merged["area_sentinel"].values

    r = np.corrcoef(x, y)[0, 1]
    rmse = np.sqrt(np.mean((y - x) ** 2))
    mae = np.mean(np.abs(y - x))
    bias = np.mean(y - x)

    metrics_df = pd.DataFrame([{
        "Reservoir": reservoir,
        "Sensor": "Sentinel-2 MSI",
        "Variable": "Area (km²)",
        "N": n,
        "Correlation_r": round(r, 3),
        "RMSE_km2": round(rmse, 3),
        "MAE_km2": round(mae, 3),
        "Bias_km2": round(bias, 3)
    }])

    metrics_file = output_path / f"sentinel_{res_key}_validation_metrics.csv"
    metrics_df.to_csv(metrics_file, index=False)
    print(f"Validation metrics saved to: {metrics_file}")
    print("\n" + metrics_df.to_string(index=False))

    # Plot validation figures (a) Time series & (b) 1:1 Dispersion
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1.4, 1.0]})

    dates = pd.to_datetime(merged["date"])

    # (a) Time Series
    ax1.plot(dates, merged["area_obs"], "o-", label="In Situ Reference (Bathymetry)", color="#1f77b4", lw=1.8, markersize=4)
    ax1.plot(dates, merged["area_sentinel"], "s--", label="Sentinel-2 NDWI", color="#ff7f0e", lw=1.5, markersize=5)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Surface Water Area (km²)")
    ax1.set_title(f"(a) Area Time Series — {reservoir.replace('_', ' ').title()}")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="best", frameon=True)

    # (b) Scatter Plot 1:1
    min_v = min(x.min(), y.min())
    max_v = max(x.max(), y.max())
    pad = max(0.1, (max_v - min_v) * 0.1)
    line_v = np.linspace(min_v - pad, max_v + pad, 100)

    ax2.plot(line_v, line_v, "k--", label="1:1 Line", lw=1.2)
    ax2.scatter(x, y, color="#ff7f0e", edgecolor="black", s=45, zorder=4)

    stats_str = (
        f"$N = {n}$\n"
        f"$r = {r:.3f}$\n"
        f"RMSE = {rmse:.3f} km²\n"
        f"MAE = {mae:.3f} km²\n"
        f"Bias = {bias:+.3f} km²"
    )
    ax2.text(0.05, 0.95, stats_str, transform=ax2.transAxes, verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9))

    ax2.set_xlabel("Observed Reference Area (km²)")
    ax2.set_ylabel("Sentinel-2 Estimated Area (km²)")
    ax2.set_title("(b) 1:1 Dispersion Diagram")
    ax2.set_xlim(min_v - pad, max_v + pad)
    ax2.set_ylim(min_v - pad, max_v + pad)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="lower right", frameon=True)

    fig.tight_layout()
    plot_file = output_path / f"sentinel_{res_key}_validation_plot.png"
    fig.savefig(plot_file)
    plt.close(fig)
    print(f"Validation plot saved to: {plot_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Sentinel-2 area time series against in situ data.")
    parser.add_argument("--sentinel", required=True, help="Path to Sentinel-2 time series CSV")
    parser.add_argument("--obs", required=True, help="Path to in situ observations CSV")
    parser.add_argument("--output", required=True, help="Output destination folder")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Target reservoir")
    args = parser.parse_args()

    validate_sentinel(args.sentinel, args.obs, args.output, args.reservoir)
