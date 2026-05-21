import pandas as pd
from pathlib import Path
import argparse


def load_if_exists(path):

    if path.exists():
        return pd.read_csv(path)

    return None


def summary_report(output_dir):

    output_dir = Path(output_dir)

    csv_dir = output_dir / "csv"

    stats = load_if_exists(csv_dir / "wse_stats_combined.csv")
    quality = load_if_exists(csv_dir / "wse_quality.csv")
    bitwise = load_if_exists(csv_dir / "wse_bitwise_flags.csv")
    temporal = load_if_exists(csv_dir / "temporal_summary.csv")

    report = {}

    if stats is not None:

        report["scenes"] = len(stats)
        report["mean_wse"] = stats["raw_mean"].mean()
        report["std_wse"] = stats["raw_mean"].std()

    if quality is not None:

        report["mean_pct_good"] = quality["pct_good"].mean()
        report["mean_pct_degraded"] = quality["pct_degraded"].mean()

    if temporal is not None:

        report["temporal_outliers"] = temporal["n_outliers"].iloc[0]

    if bitwise is not None:

        # detectar los 5 flags más frecuentes
        bit_cols = [c for c in bitwise.columns if c != "date"]

        means = bitwise[bit_cols].mean()

        top_flags = means.sort_values(ascending=False).head(5)

        for i, (flag, val) in enumerate(top_flags.items()):

            report[f"top_flag_{i+1}"] = flag
            report[f"top_flag_{i+1}_pct"] = val

    report_df = pd.DataFrame([report])

    out_file = csv_dir / "summary_report.csv"

    report_df.to_csv(out_file, index=False)

    print(f"Summary report saved: {out_file}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    summary_report(args.output)