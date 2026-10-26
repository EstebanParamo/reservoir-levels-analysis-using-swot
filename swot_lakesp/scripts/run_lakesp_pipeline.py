#!/usr/bin/env python3
"""
run_lakesp_pipeline.py
----------------------
Master orchestrator for the SWOT L2_HR_LakeSP Vector Processing and Validation Pipeline.

Executes sequentially:
    1. extract_lake_attributes.py: Ingests raw shapefiles/zips and extracts attributes.
    2. resolve_layover.py: Resolves water-water layover and filters target reservoirs.
    3. volume_estimation.py: Converts elevation to volume via official rating curves.
    4. quality_analysis.py: Computes categorical quality distribution (Table 5).
    5. bitwise_decoder.py: Decodes qual_f_b 32-bit physical error causes (Table 6).
    6. uncertainty_analysis.py: Compares declared uncertainties against in situ errors.
    7. figures_generator.py: Generates publication-ready figures.

Usage:
    python scripts/run_lakesp_pipeline.py \
      --lakesp_dir "/path/to/swot_lakesp_zips" \
      --obs_csv "/path/to/gauge_obs.csv" \
      --output "/path/to/results" \
      --reservoir "chuza"
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(script_path, args):
    cmd = [sys.executable, str(script_path)] + args
    print(f"\n---> Running: {script_path.name}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error executing {script_path.name}. Pipeline aborted.")
        sys.exit(1)


def execute_pipeline(lakesp_dir, obs_csv, output_dir, reservoir, pipeline_dir):
    pipeline_dir = Path(pipeline_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    res_key = reservoir.lower().replace(" ", "_")

    print("=================================================================")
    print(f" STARTING SWOT LAKESP PIPELINE: {reservoir.upper()}")
    print("=================================================================")

    # 1. Extraction
    raw_csv = output_dir / f"lakesp_{res_key}_raw.csv"
    run_step(
        pipeline_dir / "extract_lake_attributes.py",
        ["--input", str(lakesp_dir), "--output", str(output_dir), "--target", res_key]
    )

    # 2. Layover & Disambiguation
    clean_csv = output_dir / f"lakesp_{res_key}_clean.csv"
    run_step(
        pipeline_dir / "resolve_layover.py",
        ["--input", str(raw_csv), "--output", str(output_dir), "--reservoir", res_key]
    )

    # 3. Volume Estimation
    vol_csv = output_dir / f"lakesp_{res_key}_with_volume.csv"
    run_step(
        pipeline_dir / "volume_estimation.py",
        ["--input", str(clean_csv), "--obs", str(obs_csv), "--output", str(output_dir), "--reservoir", res_key]
    )

    # 4. Categorical Quality Analysis
    run_step(
        pipeline_dir / "quality_analysis.py",
        ["--input", str(clean_csv), "--output", str(output_dir), "--reservoir", res_key]
    )

    # 5. Bitwise Quality Decoding
    run_step(
        pipeline_dir / "bitwise_decoder.py",
        ["--input", str(clean_csv), "--output", str(output_dir), "--reservoir", res_key]
    )

    # 6. Uncertainty & Error Cross-Validation
    comparison_csv = output_dir / f"lakesp_{res_key}_uncertainty_comparison.csv"
    run_step(
        pipeline_dir / "uncertainty_analysis.py",
        ["--input", str(vol_csv), "--obs", str(obs_csv), "--output", str(output_dir), "--reservoir", res_key]
    )

    # 7. Scientific Figures Generation
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    run_step(
        pipeline_dir / "figures_generator.py",
        ["--input", str(comparison_csv), "--output", str(figures_dir), "--reservoir", res_key]
    )

    print("\n=================================================================")
    print(f" SWOT LAKESP PIPELINE COMPLETED SUCCESSFULLY FOR: {reservoir.upper()}")
    print(f" All outputs and figures saved to: {output_dir}")
    print("=================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master orchestrator for SWOT LakeSP pipeline.")
    parser.add_argument("--lakesp_dir", required=True, help="Folder containing raw LakeSP ZIPs or shapefiles")
    parser.add_argument("--obs_csv", required=True, help="Path to official in situ observations CSV")
    parser.add_argument("--output", required=True, help="Output destination folder")
    parser.add_argument("--reservoir", required=True, choices=["chuza", "san_rafael"], help="Target reservoir")
    parser.add_argument("--pipeline_dir", default=None, help="Directory containing scripts (defaults to script parent)")

    args = parser.parse_args()

    pip_dir = Path(args.pipeline_dir) if args.pipeline_dir else Path(__file__).resolve().parent
    execute_pipeline(args.lakesp_dir, args.obs_csv, args.output, args.reservoir, pip_dir)
