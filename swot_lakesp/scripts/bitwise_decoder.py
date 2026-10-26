#!/usr/bin/env python3
"""
bitwise_decoder.py (LakeSP)
---------------------------
Decodes the 32-bit integer quality flag (qual_f_b) from the SWOT L2_HR_LakeSP
product version D into physical and algorithmic condition flags.

According to NASA/CNES SWOT Level-2 Lake Single-Pass Product Specifications:
- Bit 0: classification_qual_suspect
- Bit 1: geolocation_qual_suspect
- Bit 2: water_fraction_suspect
- Bit 3: wse_std_suspect
- Bit 4: few_open_water_suspect
- Bit 5: no_prior_suspect
- Bit 6: partial_lake_suspect
- Bit 7: sig0_qual_suspect
- Bit 8: boundary_layer_suspect
- Bit 9: dark_water_suspect
- Bit 10: bad_elevation_suspect

Outputs:
    - lakesp_{reservoir}_decoded_bits.csv (per-pass boolean flags)
    - lakesp_{reservoir}_error_frequencies.csv (frequency distribution, Table 6 in paper)
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

LAKESP_BITS = {
    0: "classification_qual_suspect",
    1: "geolocation_qual_suspect",
    2: "water_fraction_suspect",
    3: "wse_std_suspect",
    4: "few_open_water_suspect",
    5: "no_prior_suspect",
    6: "partial_lake_suspect",
    7: "sig0_qual_suspect",
    8: "boundary_layer_suspect",
    9: "dark_water_suspect",
    10: "bad_elevation_suspect"
}


def decode_qual_f_b(value):
    """Decodes a single integer value into a dictionary of active flag conditions."""
    if pd.isna(value) or value < 0:
        return {flag_name: 0 for flag_name in LAKESP_BITS.values()}
    int_val = int(value)
    return {
        flag_name: 1 if ((int_val >> bit_idx) & 1) else 0
        for bit_idx, flag_name in LAKESP_BITS.items()
    }


def process_bitwise_flags(input_csv, output_dir, reservoir):
    input_file = Path(input_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)
    if "qual_f_b" not in df.columns:
        raise ValueError(f"Column 'qual_f_b' not found in {input_file.name}")

    # Decode rows
    decoded_list = [decode_qual_f_b(v) for v in df["qual_f_b"]]
    df_flags = pd.DataFrame(decoded_list)

    # Attach pass metadata
    meta_cols = [c for c in ["date", "time_str", "lake_name", "wse", "quality_f", "qual_f_b"] if c in df.columns]
    df_combined = pd.concat([df[meta_cols], df_flags], axis=1)

    res_key = reservoir.lower().replace(" ", "_")
    decoded_file = output_path / f"lakesp_{res_key}_decoded_bits.csv"
    df_combined.to_csv(decoded_file, index=False)
    print(f"Per-pass decoded bitwise flags saved to: {decoded_file}")

    # Compute frequency of active flags across all valid version D passes
    valid_passes = df[df["qual_f_b"] >= 0]
    n_valid = len(valid_passes)
    freq_data = []

    if n_valid > 0:
        for bit_idx, flag_name in LAKESP_BITS.items():
            count = df_flags[flag_name].sum()
            freq_pct = (count / n_valid) * 100.0
            freq_data.append({
                "bit": bit_idx,
                "cause": flag_name,
                "count": count,
                "total_passes": n_valid,
                "frequency_pct": round(freq_pct, 2)
            })

    df_freq = pd.DataFrame(freq_data).sort_values(by="frequency_pct", ascending=False)
    freq_file = output_path / f"lakesp_{res_key}_error_frequencies.csv"
    df_freq.to_csv(freq_file, index=False)
    print(f"Flag frequency table saved to: {freq_file}")
    print("\nTop dominant error causes:")
    print(df_freq.head(5).to_string(index=False))
    return df_combined, df_freq


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode SWOT LakeSP bitwise quality flags.")
    parser.add_argument("--input", required=True, help="Path to cleaned LakeSP CSV")
    parser.add_argument("--output", required=True, help="Folder to save decoded flags")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Reservoir name")
    args = parser.parse_args()

    process_bitwise_flags(args.input, args.output, args.reservoir)
