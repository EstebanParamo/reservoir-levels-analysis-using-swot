# -------------------------------------------------------
# compute_statistics.py
# Compute WSE statistics from clipped SWOT rasters
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import numpy as np
import pandas as pd
import rasterio
from pathlib import Path
import re


# -------------------------------------------------------
# DEFAULT PHYSICAL LIMITS (meters)
# -------------------------------------------------------

DEFAULT_MIN = 2700
DEFAULT_MAX = 3000


def extract_date(filename):
    """
    Extract date from filename
    Example: wse_2023-12-17.tif
    """
    m = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return m.group(1) if m else None


def stats(arr):

    if np.isnan(arr).all():
        return {
            "mean": np.nan,
            "min": np.nan,
            "max": np.nan,
            "std": np.nan
        }

    return {
        "mean": float(np.nanmean(arr)),
        "min": float(np.nanmin(arr)),
        "max": float(np.nanmax(arr)),
        "std": float(np.nanstd(arr))
    }


def compute_statistics(output_dir,
                       percentiles=(5,95),
                       std_factor=2,
                       min_val=None,
                       max_val=None):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped" / "wse"

    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    # ---------------------------------------------------
    # APPLY DEFAULT LIMITS IF USER DID NOT PROVIDE THEM
    # ---------------------------------------------------

    if min_val is None or max_val is None:

        print(
            f"\nUsing default physical limits: "
            f"{DEFAULT_MIN} – {DEFAULT_MAX} m"
        )

        min_val = DEFAULT_MIN
        max_val = DEFAULT_MAX

    # ---------------------------------------------------
    # FILTER ONLY TRUE WSE FILES
    # ---------------------------------------------------

    files = []

    for f in clipped_dir.glob("*.tif"):

        name = f.name

        # accept only: wse_YYYY-MM-DD.tif
        if re.match(r"^wse_\d{4}-\d{2}-\d{2}\.tif$", name):
            files.append(f)

    files = sorted(files)

    print(f"\nWSE rasters detected: {len(files)}\n")

    rows = []

    for f in files:

        date = extract_date(f.name)

        with rasterio.open(f) as src:

            data = src.read(1).astype(float)

            if src.nodata is not None:
                data[data == src.nodata] = np.nan

        # -------------------
        # RAW
        # -------------------

        raw = stats(data)

        # -------------------
        # LIMITS FILTER
        # -------------------

        mask_limits = (data >= min_val) & (data <= max_val)

        limits = stats(np.where(mask_limits, data, np.nan))

        # -------------------
        # PERCENTILES FILTER
        # -------------------

        try:

            pmin, pmax = np.nanpercentile(data, percentiles)

            mask_per = (data >= pmin) & (data <= pmax)

            percentile = stats(np.where(mask_per, data, np.nan))

        except Exception:

            percentile = {
                "mean": np.nan,
                "min": np.nan,
                "max": np.nan,
                "std": np.nan
            }

        # -------------------
        # K STD FILTER
        # -------------------

        mean = np.nanmean(data)
        std = np.nanstd(data)

        mask_std = (
            (data >= mean - std_factor * std) &
            (data <= mean + std_factor * std)
        )

        kstd = stats(np.where(mask_std, data, np.nan))

        # -------------------
        # STORE RESULT
        # -------------------

        row = {

            "date": date,

            "raw_mean": raw["mean"],
            "raw_min": raw["min"],
            "raw_max": raw["max"],
            "raw_std": raw["std"],

            "limits_mean": limits["mean"],
            "limits_min": limits["min"],
            "limits_max": limits["max"],
            "limits_std": limits["std"],

            "percentile_mean": percentile["mean"],
            "percentile_min": percentile["min"],
            "percentile_max": percentile["max"],
            "percentile_std": percentile["std"],

            "kstd_mean": kstd["mean"],
            "kstd_min": kstd["min"],
            "kstd_max": kstd["max"],
            "kstd_std": kstd["std"]

        }

        rows.append(row)

    df = pd.DataFrame(rows)

    # sort by date
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    out_csv = csv_dir / "wse_statistics.csv"

    df.to_csv(out_csv, index=False)

    print(f"\nStatistics saved: {out_csv}\n")


# -------------------------------------------------------
# Standalone execution
# -------------------------------------------------------

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Compute WSE statistics"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Results directory"
    )

    parser.add_argument(
        "--percentiles",
        nargs=2,
        type=float,
        default=[5,95]
    )

    parser.add_argument(
        "--std_factor",
        type=float,
        default=2
    )

    parser.add_argument(
        "--min",
        type=float
    )

    parser.add_argument(
        "--max",
        type=float
    )

    args = parser.parse_args()

    compute_statistics(
        output_dir=args.output,
        percentiles=args.percentiles,
        std_factor=args.std_factor,
        min_val=args.min,
        max_val=args.max
    )