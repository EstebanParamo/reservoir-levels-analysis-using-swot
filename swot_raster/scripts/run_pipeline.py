import subprocess
import argparse
from pathlib import Path
import sys


def run_script(script, args):

    cmd = [sys.executable, script] + args

    print("\nRunning:", script)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"Error running {script}")
        sys.exit(1)


def run_pipeline(nc_dir, shape, output, pipeline_dir):

    pipeline_dir = Path(pipeline_dir)

    scripts = [

        # ---------------------------------------
        # 1. Extract raster layers from NetCDF
        # ---------------------------------------

        ("extract_layers.py",
         ["--input", nc_dir, "--output", output]),

        # ---------------------------------------
        # 2. Build mosaics
        # ---------------------------------------

        ("mosaic.py",
         ["--output", output]),

        # ---------------------------------------
        # 3. Clip rasters to reservoir polygon
        # ---------------------------------------

        ("clip.py",
         ["--shape", shape, "--output", output]),

        # ---------------------------------------
        # 4. Compute WSE statistics
        # ---------------------------------------

        ("compute_statistics.py",
         ["--output", output]),

        # ---------------------------------------
        # 5. Quality categories analysis
        # ---------------------------------------

        ("quality_analysis.py",
         ["--output", output]),

        # ---------------------------------------
        # 6. Decode bitwise flags
        # ---------------------------------------

        ("bitwise_decoder.py",
         ["--output", output]),

        # ---------------------------------------
        # 7. Spatial frequency of errors
        # ---------------------------------------

        ("error_frequency_maps.py",
         ["--output", output]),

        # ---------------------------------------
        # 8. Summary tables of errors
        # ---------------------------------------

        ("error_summary_tables.py",
         ["--output", output]),

        # ---------------------------------------
        # 9. Water surface coverage analysis
        # ---------------------------------------

        ("coverage_analysis.py",
         ["--output", output, "--shape", shape]),

        # ---------------------------------------
        # 10. Temporal diagnostics
        # ---------------------------------------

        ("temporal_diagnostics.py",
         ["--output", output]),

        # ---------------------------------------
        # 11. Figures generator
        # ---------------------------------------

        ("figures_generator.py",
         ["--output", output]),

        # ---------------------------------------
        # 12. Summary report
        # ---------------------------------------

        ("summary_report.py",
         ["--output", output])
    ]

    for script, args in scripts:

        script_path = pipeline_dir / script

        run_script(str(script_path), args)

    print("\nPIPELINE COMPLETED SUCCESSFULLY")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--nc",
        required=True,
        help="Folder containing SWOT NetCDF files"
    )

    parser.add_argument(
        "--shape",
        required=True,
        help="Reservoir polygon"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Results folder"
    )

    parser.add_argument(
        "--pipeline",
        required=True,
        help="Pipeline scripts folder"
    )

    args = parser.parse_args()

    run_pipeline(
        args.nc,
        args.shape,
        args.output,
        args.pipeline
    )