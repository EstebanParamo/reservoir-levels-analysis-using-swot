import rasterio
import numpy as np
import pandas as pd
from pathlib import Path
import re
import argparse


def extract_date(name):

    m = re.search(r"\d{4}-\d{2}-\d{2}", name)

    if m:
        return m.group(0)

    return None


def compute_quality_metrics(arr):

    arr = arr[~np.isnan(arr)]

    if arr.size == 0:
        return None

    total = arr.size

    good = np.sum(arr == 0)
    suspect = np.sum(arr == 1)
    degraded = np.sum(arr == 2)
    bad = np.sum(arr == 3)

    return {

        "pct_good": good / total * 100,
        "pct_suspect": suspect / total * 100,
        "pct_degraded": degraded / total * 100,
        "pct_bad": bad / total * 100,
        "mean_quality": np.mean(arr)

    }


import rasterio
import numpy as np
import pandas as pd
from pathlib import Path
import re
import argparse


def extract_date(name):

    m = re.search(r"\d{4}-\d{2}-\d{2}", name)

    if m:
        return m.group(0)

    return None


def compute_quality_metrics(arr):

    arr = arr[~np.isnan(arr)]

    if arr.size == 0:
        return None

    total = arr.size

    good = np.sum(arr == 0)
    suspect = np.sum(arr == 1)
    degraded = np.sum(arr == 2)
    bad = np.sum(arr == 3)

    return {

        "pct_good": good / total * 100,
        "pct_suspect": suspect / total * 100,
        "pct_degraded": degraded / total * 100,
        "pct_bad": bad / total * 100,
        "mean_quality": np.mean(arr)

    }


def process_variable(var_dir):

    files = list(var_dir.glob("*qual*.tif"))

    # eliminar bitwise
    files = [f for f in files if "bitwise" not in f.name]

    rows = []

    for f in files:

        date = extract_date(f.name)

        with rasterio.open(f) as src:

            arr = src.read(1).astype(float)

            if src.nodata is not None:
                arr[arr == src.nodata] = np.nan

        metrics = compute_quality_metrics(arr)

        if metrics is None:
            continue

        row = {"date": date}
        row.update(metrics)

        rows.append(row)

    return pd.DataFrame(rows)


def quality_analysis(output_dir):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped"

    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    variables = {

        "wse": "wse_quality.csv",
        "area": "area_quality.csv",
        "sig0": "sig0_quality.csv"
    }

    for var, csv_name in variables.items():

        print(f"\nProcessing {var}")

        var_dir = clipped_dir / var

        if not var_dir.exists():
            print("Directory not found")
            continue

        df = process_variable(var_dir)

        if df.empty:
            print("No quality files found")
            continue

        out_csv = csv_dir / csv_name

        df.sort_values("date").to_csv(out_csv, index=False)

        print(f"Saved: {out_csv}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    quality_analysis(args.output)

def quality_analysis(output_dir):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped"

    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    variables = {

        "wse": "wse_quality.csv",
        "area": "area_quality.csv",
        "sig0": "sig0_quality.csv"
    }

    for var, csv_name in variables.items():

        print(f"\nProcessing {var}")

        var_dir = clipped_dir / var

        if not var_dir.exists():
            print("Directory not found")
            continue

        df = process_variable(var_dir)

        if df.empty:
            print("No quality files found")
            continue

        out_csv = csv_dir / csv_name

        df.sort_values("date").to_csv(out_csv, index=False)

        print(f"Saved: {out_csv}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    quality_analysis(args.output)