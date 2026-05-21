import rasterio
import numpy as np
import pandas as pd
from pathlib import Path
import re
import argparse


# ------------------------------------------------------
# Bit definitions (NASA Table 15)
# ------------------------------------------------------

WSE_BITS = {

0:"sig0_qual_suspect",
1:"classification_qual_suspect",
2:"geolocation_qual_suspect",
5:"large_uncert_suspect",
6:"dark_water_suspect",
7:"bright_land",
9:"specular_ringing_prior_water_suspect",
12:"few_pixels",
13:"far_range_suspect",
14:"near_range_suspect",

18:"classification_qual_degraded",
19:"geolocation_qual_degraded",
20:"dark_water_degraded",
21:"low_coherence_water_degraded",
22:"specular_ringing_prior_land_degraded",

24:"value_bad",
26:"outside_data_window",
28:"no_pixels",
29:"outside_scene_bounds",
30:"inner_swath",
31:"missing_karin_data"

}

AREA_BITS = {

1:"classification_qual_suspect",
2:"geolocation_qual_suspect",
3:"water_fraction_suspect",
5:"large_uncert_suspect",
6:"dark_water_suspect",
7:"bright_land",
8:"low_coherence_water_suspect",
9:"specular_ringing_prior_water_suspect",
10:"specular_ringing_prior_land_suspect",
12:"few_pixels",
13:"far_range_suspect",
14:"near_range_suspect",

18:"classification_qual_degraded",
19:"geolocation_qual_degraded",

24:"value_bad",
26:"outside_data_window",
28:"no_pixels",
29:"outside_scene_bounds",
30:"inner_swath",
31:"missing_karin_data"

}

SIG0_BITS = {

0:"sig0_qual_suspect",
1:"classification_qual_suspect",
2:"geolocation_qual_suspect",
5:"large_uncert_suspect",
6:"dark_water_suspect",
7:"bright_land",
8:"low_coherence_water_suspect",
9:"specular_ringing_prior_water_suspect",
10:"specular_ringing_prior_land_suspect",
12:"few_pixels",
13:"far_range_suspect",
14:"near_range_suspect",

17:"sig0_qual_degraded",
18:"classification_qual_degraded",
19:"geolocation_qual_degraded",

24:"value_bad",
26:"outside_data_window",
28:"no_pixels",
29:"outside_scene_bounds",
30:"inner_swath",
31:"missing_karin_data"

}


# ------------------------------------------------------

def extract_date(name):

    m = re.search(r"\d{4}-\d{2}-\d{2}", name)

    if m:
        return m.group(0)

    return None


# ------------------------------------------------------

def decode_bits(arr, bit):

    return ((arr.astype(np.uint32) >> bit) & 1)


# ------------------------------------------------------

def compute_bitwise_stats(arr, bit_dict):

    arr = arr[~np.isnan(arr)]

    total = arr.size

    stats = {}

    for bit, name in bit_dict.items():

        decoded = decode_bits(arr, bit)

        pct = np.sum(decoded) / total * 100

        column_name = f"bit_{bit}_{name}"

        stats[column_name] = pct

    return stats


# ------------------------------------------------------

def process_variable(var_dir, bit_dict):

    files = sorted(var_dir.glob("*bitwise*.tif"))

    rows = []

    for f in files:

        date = extract_date(f.name)

        if date is None:
            continue

        with rasterio.open(f) as src:

            arr = src.read(1)

            if src.nodata is not None:

                arr = arr.astype(float)
                arr[arr == src.nodata] = np.nan

        stats = compute_bitwise_stats(arr, bit_dict)

        row = {"date": date}

        row.update(stats)

        rows.append(row)

    return pd.DataFrame(rows)


# ------------------------------------------------------

def bitwise_analysis(output_dir):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped"

    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    variables = {

        "wse": (WSE_BITS, "wse_bitwise_flags.csv"),
        "area": (AREA_BITS, "area_bitwise_flags.csv"),
        "sig0": (SIG0_BITS, "sig0_bitwise_flags.csv")

    }

    for var, (bit_dict, csv_name) in variables.items():

        print(f"\nProcessing {var}")

        var_dir = clipped_dir / var

        if not var_dir.exists():
            print("Directory not found")
            continue

        df = process_variable(var_dir, bit_dict)

        if df.empty:
            print("No bitwise files found")
            continue

        out_csv = csv_dir / csv_name

        df.sort_values("date").to_csv(out_csv, index=False)

        print(f"Saved: {out_csv}")


# ------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    bitwise_analysis(args.output)