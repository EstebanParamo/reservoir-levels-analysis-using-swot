import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def load_csv(csv_dir, name):

    f = csv_dir / name

    if not f.exists():
        print(f"{name} not found")
        return None

    return pd.read_csv(f)


# ---------------------------
# WSE TIME SERIES
# ---------------------------

def plot_wse_timeseries(stats, out_dir):

    stats["date"] = pd.to_datetime(stats["date"])

    series = pd.to_numeric(stats["kstd_mean"], errors="coerce")

    # eliminar valores absurdos
    mask = (series > 2000) & (series < 4000)

    stats = stats[mask]
    series = series[mask]

    plt.figure(figsize=(10,5))

    plt.plot(stats["date"], series, marker="o")

    plt.title("Reservoir Water Surface Elevation (WSE)")
    plt.xlabel("Date")
    plt.ylabel("Elevation (m)")

    plt.grid(True)

    plt.tight_layout()

    out_file = out_dir / "wse_timeseries.png"

    plt.savefig(out_file, dpi=300)

    plt.close()

    print("Saved:", out_file)


# ---------------------------
# HISTOGRAM
# ---------------------------

def plot_wse_histogram(stats, out_dir):

    series = pd.to_numeric(stats["kstd_mean"], errors="coerce")

    series = series[(series > 2000) & (series < 4000)]

    plt.figure(figsize=(8,5))

    plt.hist(series, bins=15)

    plt.title("Distribution of Water Surface Elevation")
    plt.xlabel("Elevation (m)")
    plt.ylabel("Frequency")

    plt.tight_layout()

    out_file = out_dir / "wse_histogram.png"

    plt.savefig(out_file, dpi=300)

    plt.close()

    print("Saved:", out_file)

def plot_wse_vs_quality(stats, quality_df, out_dir):

    stats["date"] = pd.to_datetime(stats["date"])
    quality_df["date"] = pd.to_datetime(quality_df["date"])

    # unir datasets por fecha
    df = stats.merge(quality_df, on="date", how="inner")

    series = pd.to_numeric(df["kstd_mean"], errors="coerce")

    mask = (series > 2000) & (series < 4000)

    df = df[mask]

    fig, ax1 = plt.subplots(figsize=(10,5))

    # eje izquierdo → WSE
    ax1.plot(df["date"], df["kstd_mean"], marker="o")
    ax1.set_ylabel("WSE (m)")

    # eje derecho → calidad
    ax2 = ax1.twinx()

    ax2.plot(df["date"], df["mean_quality"], linestyle="--")

    ax2.set_ylabel("Mean Quality Flag")

    ax1.set_xlabel("Date")

    ax1.set_title("Water Surface Elevation vs Measurement Quality")

    ax1.grid(True)

    plt.tight_layout()

    out_file = out_dir / "wse_vs_quality.png"

    plt.savefig(out_file, dpi=300)

    plt.close()

    print("Saved:", out_file)

# ---------------------------
# QUALITY DISTRIBUTION
# ---------------------------

def plot_quality(df, variable, out_dir):

    cols = [
        "pct_good",
        "pct_suspect",
        "pct_degraded",
        "pct_bad"
    ]

    # media simple
    values = df[cols].mean()

    labels = [
        "Good",
        "Suspect",
        "Degraded",
        "Bad"
    ]

    plt.figure(figsize=(7,5))

    plt.bar(labels, values)

    plt.ylabel("Percentage")

    plt.title(f"{variable.upper()} Quality Distribution")

    plt.ylim(0,100)

    plt.tight_layout()

    out_file = out_dir / f"{variable}_quality_distribution.png"

    plt.savefig(out_file, dpi=300)

    plt.close()

    print("Saved:", out_file)


# ---------------------------
# MAIN
# ---------------------------

def generate_figures(output_dir):

    output_dir = Path(output_dir)

    csv_dir = output_dir / "csv"

    fig_dir = output_dir / "figures"

    fig_dir.mkdir(exist_ok=True)

    print("\nGenerating figures")

    stats = load_csv(csv_dir, "wse_statistics.csv")

    if stats is not None:

        plot_wse_timeseries(stats, fig_dir)

        plot_wse_histogram(stats, fig_dir)

    wse_q = load_csv(csv_dir, "wse_quality.csv")
    area_q = load_csv(csv_dir, "area_quality.csv")
    sig0_q = load_csv(csv_dir, "sig0_quality.csv")

    if wse_q is not None:
        plot_quality(wse_q, "wse", fig_dir)

    if area_q is not None:
        plot_quality(area_q, "area", fig_dir)

    if sig0_q is not None:
        plot_quality(sig0_q, "sig0", fig_dir)

    print("\nFigures created successfully")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    generate_figures(args.output)