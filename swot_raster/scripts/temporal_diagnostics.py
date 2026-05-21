import pandas as pd
from pathlib import Path
import argparse


def detect_outliers(series, k=2):

    mean = series.mean()
    std = series.std()

    lower = mean - k * std
    upper = mean + k * std

    return (series < lower) | (series > upper)


def temporal_diagnostics(output_dir):

    output_dir = Path(output_dir)

    csv_dir = output_dir / "csv"

    stats_file = csv_dir / "wse_statistics.csv"

    if not stats_file.exists():
        print("wse_statistics.csv not found")
        return

    print(f"Using stats file: {stats_file.name}")

    stats = pd.read_csv(stats_file)

    # --------------------------------------------------
    # preparar fechas
    # --------------------------------------------------

    stats["date"] = pd.to_datetime(stats["date"])

    stats = stats.sort_values("date")

    # --------------------------------------------------
    # usar estimador robusto
    # --------------------------------------------------

    if "kstd_mean" not in stats.columns:
        print("kstd_mean column not found")
        return

    series = pd.to_numeric(stats["kstd_mean"], errors="coerce")

    # --------------------------------------------------
    # eliminar valores absurdos
    # (seguridad adicional)
    # --------------------------------------------------

    series = series[(series > 2000) & (series < 4000)]

    series = series.dropna()

    stats = stats.loc[series.index]

    # --------------------------------------------------
    # detectar outliers
    # --------------------------------------------------

    stats["temporal_outlier"] = detect_outliers(series)

    # --------------------------------------------------
    # guardar diagnóstico temporal
    # --------------------------------------------------

    out_file = csv_dir / "temporal_diagnostics.csv"

    stats.to_csv(out_file, index=False)

    print(f"Temporal diagnostics saved: {out_file}")

    # --------------------------------------------------
    # resumen temporal
    # --------------------------------------------------

    summary = {

        "mean_wse": series.mean(),
        "std_wse": series.std(),
        "min_wse": series.min(),
        "max_wse": series.max(),
        "n_outliers": int(stats["temporal_outlier"].sum()),
        "n_scenes": int(len(series))

    }

    summary_df = pd.DataFrame([summary])

    summary_file = csv_dir / "temporal_summary.csv"

    summary_df.to_csv(summary_file, index=False)

    print(f"Temporal summary saved: {summary_file}")


# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    temporal_diagnostics(args.output)