# -------------------------------------------------------
# error_summary_tables.py
# Generate summary tables of SWOT quality bitwise errors
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import rasterio
import numpy as np
import pandas as pd
from pathlib import Path
import re
import argparse

FILL_VALUE = 4294967295


BIT_NAMES = {

    1: "dark_water",
    2: "low_coherence",
    12: "classification_degraded",
    14: "land_contamination",
    19: "geophysical_correction",
    20: "geophysical_model",
    21: "atmospheric_correction",
    26: "sig0_quality_degraded",
    28: "geolocation_uncertainty",
    29: "high_measurement_uncertainty"

}


def extract_date(name):

    m = re.search(r"\d{4}-\d{2}-\d{2}", name)

    if m:
        return m.group(0)

    return None


def detect_active_bits(files):

    bits = set()

    for f in files:

        with rasterio.open(f) as src:

            arr = src.read(1).astype("uint32")

            arr[arr == FILL_VALUE] = 0

        for b in range(32):

            if np.any(((arr >> b) & 1) == 1):
                bits.add(b)

    return sorted(bits)


def process_variable(var_dir, csv_dir, var_name):

    files = sorted([

        f for f in var_dir.glob("*qual_bitwise*.tif")

    ])

    if len(files) == 0:

        print(f"No bitwise files for {var_name}")
        return

    print(f"\nProcessing {var_name} ({len(files)} scenes)")

    bits = detect_active_bits(files)

    print("Active bits:", bits)

    # -----------------------------
    # TABLE B — ERROR BY DATE
    # -----------------------------

    rows = []

    for f in files:

        date = extract_date(f.name)

        with rasterio.open(f) as src:

            arr = src.read(1).astype("uint32")

            arr[arr == FILL_VALUE] = 0

        total_pixels = arr.size

        row = {"date": date}

        for b in bits:

            mask = ((arr >> b) & 1)

            pct = np.sum(mask) / total_pixels * 100

            row[f"bit{b}_{BIT_NAMES.get(b,'unknown')}"] = pct

        rows.append(row)

    df_date = pd.DataFrame(rows)

    df_date["date"] = pd.to_datetime(df_date["date"])
    df_date = df_date.sort_values("date")

    out_date = csv_dir / f"error_by_date_{var_name}.csv"

    df_date.to_csv(out_date, index=False)

    print("Saved:", out_date)

    # -----------------------------
    # TABLE A — GLOBAL SUMMARY
    # -----------------------------

    summary_rows = []

    pixel_occurrence = {b: 0 for b in bits}
    pixel_presence = {b: None for b in bits}

    n_scenes = len(files)

    for i, f in enumerate(files):

        with rasterio.open(f) as src:

            arr = src.read(1).astype("uint32")

            arr[arr == FILL_VALUE] = 0

        for b in bits:

            mask = ((arr >> b) & 1)

            pixel_occurrence[b] += mask

            if pixel_presence[b] is None:
                pixel_presence[b] = mask.copy()
            else:
                pixel_presence[b] = pixel_presence[b] | mask

    for b in bits:

        mean_freq = np.mean(pixel_occurrence[b] / n_scenes * 100)

        pixels_affected = np.sum(pixel_presence[b]) / pixel_presence[b].size * 100

        summary_rows.append({

            "bit": b,
            "error_name": BIT_NAMES.get(b, "unknown"),
            "frequency_mean_percent": mean_freq,
            "pixels_affected_percent": pixels_affected

        })

    df_summary = pd.DataFrame(summary_rows)

    out_summary = csv_dir / f"error_summary_{var_name}.csv"

    df_summary.to_csv(out_summary, index=False)

    print("Saved:", out_summary)


def error_summary_tables(output_dir):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped"

    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    variables = {

        "wse": clipped_dir / "wse",
        "water_area": clipped_dir / "area",
        "sig0": clipped_dir / "sig0"

    }

    for var_name, var_dir in variables.items():

        process_variable(var_dir, csv_dir, var_name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    error_summary_tables(args.output)