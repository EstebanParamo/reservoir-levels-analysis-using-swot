#!/usr/bin/env python3
"""
figures_generator.py (LakeSP)
-----------------------------
Generates high-resolution scientific validation figures for SWOT L2_HR_LakeSP:
1. WSE validation: Time series and 1:1 scatter plot with statistical metrics (r, RMSE, MAE, Bias)
2. Area validation: Time series comparing observed area vs area_detct and area_total
3. Volume validation: In situ vs SWOT storage volume time series and scatter plot
4. Uncertainty analysis: Zero-centered error time series with declared ±wse_u and ±wse_std error bands
5. Quality diagnostics: Categorical quality distribution and top physical error causes

Outputs:
    - wse_validation_{reservoir}.png
    - area_validation_{reservoir}.png
    - volume_validation_{reservoir}.png
    - uncertainty_bands_{reservoir}.png
    - quality_distribution_{reservoir}.png
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Clean scientific plotting style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})


def compute_metrics(x, y):
    """Computes r, RMSE, MAE, and Bias."""
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_val, y_val = x[mask], y[mask]
    n = len(x_val)
    if n < 2:
        return {"n": n, "r": np.nan, "rmse": np.nan, "mae": np.nan, "bias": np.nan}
    r = np.corrcoef(x_val, y_val)[0, 1]
    rmse = np.sqrt(np.mean((y_val - x_val) ** 2))
    mae = np.mean(np.abs(y_val - x_val))
    bias = np.mean(y_val - x_val)
    return {"n": n, "r": r, "rmse": rmse, "mae": mae, "bias": bias}


def plot_wse_validation(df, output_path, reservoir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1.4, 1.0]})

    dates = pd.to_datetime(df["date"])
    wse_obs = df["wse_obs"]
    wse_swot = df["wse"]

    m = compute_metrics(wse_obs.values, wse_swot.values)

    # (a) Time series
    ax1.plot(dates, wse_obs, label="In Situ Gauge (EAAB)", color="#1f77b4", lw=2, zorder=2)
    ax1.errorbar(dates, wse_swot, yerr=df.get("wse_u", None), fmt="o", label="SWOT LakeSP",
                 color="#d62728", ecolor="#d62728", elinewidth=1.2, capsize=3, markersize=5, zorder=3)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Water Surface Elevation (m.a.s.l.)")
    ax1.set_title(f"(a) WSE Time Series — {reservoir.replace('_', ' ').title()}")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="best", frameon=True)

    # (b) Scatter plot 1:1
    min_val = min(wse_obs.min(), wse_swot.min())
    max_val = max(wse_obs.max(), wse_swot.max())
    pad = (max_val - min_val) * 0.05
    line_range = np.linspace(min_val - pad, max_val + pad, 100)

    ax2.plot(line_range, line_range, "k--", label="1:1 Line", lw=1.2)
    ax2.scatter(wse_obs, wse_swot, color="#d62728", edgecolor="black", s=40, zorder=4, alpha=0.85)

    stats_text = (
        f"$N = {m['n']}$\n"
        f"$r = {m['r']:.3f}$\n"
        f"RMSE = {m['rmse']:.3f} m\n"
        f"MAE = {m['mae']:.3f} m\n"
        f"Bias = {m['bias']:+.3f} m"
    )
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9))

    ax2.set_xlabel("Observed Elevation (m.a.s.l.)")
    ax2.set_ylabel("SWOT LakeSP Elevation (m.a.s.l.)")
    ax2.set_title(f"(b) 1:1 Dispersion Diagram")
    ax2.set_xlim(min_val - pad, max_val + pad)
    ax2.set_ylim(min_val - pad, max_val + pad)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="lower right", frameon=True)

    fig.tight_layout()
    out_file = output_path / f"wse_validation_{reservoir}.png"
    fig.savefig(out_file)
    plt.close(fig)
    print(f"Generated: {out_file.name}")


def plot_area_validation(df, output_path, reservoir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1.4, 1.0]})

    dates = pd.to_datetime(df["date"])
    area_obs = df["area_obs"]
    area_swot = df["area_used"] if "area_used" in df.columns else df.get("area_detct", df.get("area_total"))

    m = compute_metrics(area_obs.values, area_swot.values)

    ax1.plot(dates, area_obs, label="In Situ Derived (Bathymetric Rating)", color="#1f77b4", lw=2)
    ax1.scatter(dates, area_swot, label="SWOT LakeSP (Radar Detected)", color="#2ca02c", s=35, zorder=3)
    if "area_total" in df.columns and "area_detct" in df.columns and reservoir == "san_rafael":
        ax1.scatter(dates, df["area_total"], label="SWOT area_total (Corrupted by Layover)",
                    color="#ff7f0e", marker="x", s=30, alpha=0.7)

    ax1.set_xlabel("Date")
    ax1.set_ylabel("Surface Water Area (km²)")
    ax1.set_title(f"(a) Area Time Series — {reservoir.replace('_', ' ').title()}")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="best", frameon=True)

    # 1:1 Scatter
    min_val = min(area_obs.min(), area_swot.min())
    max_val = max(area_obs.max(), area_swot.max())
    pad = max(0.1, (max_val - min_val) * 0.08)
    line_range = np.linspace(min_val - pad, max_val + pad, 100)

    ax2.plot(line_range, line_range, "k--", label="1:1 Line", lw=1.2)
    ax2.scatter(area_obs, area_swot, color="#2ca02c", edgecolor="black", s=40, zorder=4)

    stats_text = (
        f"$N = {m['n']}$\n"
        f"$r = {m['r']:.3f}$\n"
        f"RMSE = {m['rmse']:.3f} km²\n"
        f"MAE = {m['mae']:.3f} km²\n"
        f"Bias = {m['bias']:+.3f} km²"
    )
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9))

    ax2.set_xlabel("Observed Reference Area (km²)")
    ax2.set_ylabel("SWOT LakeSP Area (km²)")
    ax2.set_title("(b) 1:1 Dispersion Diagram")
    ax2.set_xlim(min_val - pad, max_val + pad)
    ax2.set_ylim(min_val - pad, max_val + pad)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="lower right", frameon=True)

    fig.tight_layout()
    out_file = output_path / f"area_validation_{reservoir}.png"
    fig.savefig(out_file)
    plt.close(fig)
    print(f"Generated: {out_file.name}")


def plot_volume_validation(df, output_path, reservoir):
    if "volumen_obs" not in df.columns or "volumen_swot_hm3" not in df.columns:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1.4, 1.0]})

    dates = pd.to_datetime(df["date"])
    vol_obs = df["volumen_obs"]
    vol_swot = df["volumen_swot_hm3"]

    m = compute_metrics(vol_obs.values, vol_swot.values)

    ax1.plot(dates, vol_obs, label="Observed Storage Volume (EAAB)", color="#1f77b4", lw=2)
    ax1.scatter(dates, vol_swot, label="SWOT LakeSP Derived Volume", color="#9467bd", s=35, zorder=3)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Storage Volume (hm³)")
    ax1.set_title(f"(a) Storage Volume Time Series — {reservoir.replace('_', ' ').title()}")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="best", frameon=True)

    min_val = min(vol_obs.min(), vol_swot.min())
    max_val = max(vol_obs.max(), vol_swot.max())
    pad = (max_val - min_val) * 0.05
    line_range = np.linspace(min_val - pad, max_val + pad, 100)

    ax2.plot(line_range, line_range, "k--", label="1:1 Line", lw=1.2)
    ax2.scatter(vol_obs, vol_swot, color="#9467bd", edgecolor="black", s=40, zorder=4)

    stats_text = (
        f"$N = {m['n']}$\n"
        f"$r = {m['r']:.3f}$\n"
        f"RMSE = {m['rmse']:.3f} hm³\n"
        f"MAE = {m['mae']:.3f} hm³\n"
        f"Bias = {m['bias']:+.3f} hm³"
    )
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9))

    ax2.set_xlabel("Observed Volume (hm³)")
    ax2.set_ylabel("SWOT Derived Volume (hm³)")
    ax2.set_title("(b) 1:1 Dispersion Diagram")
    ax2.set_xlim(min_val - pad, max_val + pad)
    ax2.set_ylim(min_val - pad, max_val + pad)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="lower right", frameon=True)

    fig.tight_layout()
    out_file = output_path / f"volume_validation_{reservoir}.png"
    fig.savefig(out_file)
    plt.close(fig)
    print(f"Generated: {out_file.name}")


def plot_uncertainty_bands(df, output_path, reservoir):
    if "error_wse" not in df.columns or "wse_u" not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(12, 4.8))

    dates = pd.to_datetime(df["date"])
    err = df["error_wse"]
    u = df["wse_u"]

    ax.axhline(0, color="black", linestyle="-", lw=1.0)
    ax.fill_between(dates, -u, u, color="gray", alpha=0.3, label="Declared ±$wse\\_u$ Band")
    if "wse_std" in df.columns:
        ax.plot(dates, df["wse_std"], color="orange", linestyle=":", lw=1.2, label="+$wse\\_std$")
        ax.plot(dates, -df["wse_std"], color="orange", linestyle=":", lw=1.2, label="-$wse\\_std$")

    ax.plot(dates, err, "o-", color="#d62728", lw=1.5, markersize=5, label="Actual Error ($WSE_{SWOT} - WSE_{obs}$)")

    ax.set_xlabel("Date")
    ax.set_ylabel("Elevation Error (m)")
    ax.set_title(f"Uncertainty vs. Real Error — {reservoir.replace('_', ' ').title()}")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best", frameon=True)

    fig.tight_layout()
    out_file = output_path / f"uncertainty_bands_{reservoir}.png"
    fig.savefig(out_file)
    plt.close(fig)
    print(f"Generated: {out_file.name}")


def generate_all_figures(comparison_csv, output_dir, reservoir):
    input_file = Path(comparison_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)
    res_key = reservoir.lower().replace(" ", "_")

    plot_wse_validation(df, output_path, res_key)
    plot_area_validation(df, output_path, res_key)
    plot_volume_validation(df, output_path, res_key)
    plot_uncertainty_bands(df, output_path, res_key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LakeSP scientific validation figures.")
    parser.add_argument("--input", required=True, help="Path to uncertainty/comparison CSV")
    parser.add_argument("--output", required=True, help="Folder to save figures")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Reservoir name")
    args = parser.parse_args()

    generate_all_figures(args.input, args.output, args.reservoir)
