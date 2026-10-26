#!/usr/bin/env python3
"""
quality_analysis.py (LakeSP)
----------------------------
Evaluates the intrinsic categorical quality flag (quality_f) of SWOT L2_HR_LakeSP:
- 0: Good (high-confidence measurement)
- 1: Suspect (usable, with quality warnings)
- 2: Degraded (usable with caution, significant errors possible)
- 3: Bad (invalid, should be discarded)

Generates:
    - Categorical percentage distribution summary table (Table 5 in paper)
    - Timeline plot of quality classes across passes
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

QUALITY_LABELS = {
    0: "Good",
    1: "Suspect",
    2: "Degraded",
    3: "Bad"
}


def analyze_quality(input_csv, output_dir, reservoir):
    input_file = Path(input_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)
    if "quality_f" not in df.columns:
        raise ValueError(f"Column 'quality_f' not found in {input_file.name}")

    # Drop missing / invalid quality values
    valid_df = df.dropna(subset=["quality_f"]).copy()
    valid_df = valid_df[valid_df["quality_f"] >= 0]
    total_obs = len(valid_df)

    res_key = reservoir.lower().replace(" ", "_")
    summary = {"Reservoir": reservoir, "Total_Passes": total_obs}

    for q_code, q_label in QUALITY_LABELS.items():
        count = (valid_df["quality_f"] == q_code).sum()
        pct = (count / total_obs * 100.0) if total_obs > 0 else 0.0
        summary[f"{q_label}_count"] = count
        summary[f"{q_label}_pct"] = round(pct, 2)

    df_summary = pd.DataFrame([summary])
    summary_file = output_path / f"lakesp_{res_key}_quality_summary.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"Categorical quality distribution saved to: {summary_file}")
    print(df_summary[["Reservoir", "Total_Passes", "Good_pct", "Suspect_pct", "Degraded_pct", "Bad_pct"]].to_string(index=False))

    return df_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze SWOT LakeSP categorical quality.")
    parser.add_argument("--input", required=True, help="Cleaned LakeSP CSV")
    parser.add_argument("--output", required=True, help="Folder to save quality report")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Reservoir name")
    args = parser.parse_args()

    analyze_quality(args.input, args.output, args.reservoir)
