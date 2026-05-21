# -------------------------------------------------------
# extract_layers.py
# Extract SWOT Raster layers from NetCDF
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import os
import re
from pathlib import Path
import xarray as xr
import rioxarray


# VARIABLES QUE VAMOS A EXTRAER
VARIABLE_GROUPS = {
    "wse": [
        "wse",
        "wse_qual",
        "wse_qual_bitwise"
    ],
    "area": [
        "water_area",
        "water_area_qual",
        "water_area_qual_bitwise"
    ],
    "sig0": [
        "sig0",
        "sig0_qual",
        "sig0_qual_bitwise"
    ]
}


def parse_filename(filename):
    """
    Extract date and tile from SWOT filename.
    Example:
    SWOT_L2_HR_Raster_..._073F_20231217T233243...
    """

    date_match = re.search(r"_(\d{8})T", filename)
    tile_match = re.search(r"_(\d{3}F)_", filename)

    if not date_match or not tile_match:
        return None, None

    date = date_match.group(1)
    date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"

    tile = tile_match.group(1)

    return date, tile


def ensure_directories(output_dir):
    """
    Create folder structure.
    """

    layers_dir = Path(output_dir) / "layers"

    dirs = {
        "wse": layers_dir / "wse",
        "area": layers_dir / "area",
        "sig0": layers_dir / "sig0"
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    return dirs


def extract_layers(input_dir, output_dir):

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    dirs = ensure_directories(output_dir)

    nc_files = sorted(input_dir.glob("*.nc"))

    print(f"\nNetCDF files found: {len(nc_files)}")

    for nc_file in nc_files:

        print(f"\nProcessing: {nc_file.name}")

        date, tile = parse_filename(nc_file.name)

        if date is None:
            print("Skipping file (date not detected)")
            continue

        try:
            ds = xr.open_dataset(nc_file)

            for group, variables in VARIABLE_GROUPS.items():

                for var in variables:

                    if var not in ds:
                        continue

                    da = ds[var]

                    try:
                        da = da.rio.write_crs("EPSG:32618", inplace=False)
                    except Exception:
                        pass

                    out_name = f"{var}_{date}_{tile}.tif"
                    out_path = dirs[group] / out_name

                    try:
                        da.rio.to_raster(out_path, compress="LZW")
                        print(f"Saved: {out_name}")
                    except Exception as e:
                        print(f"Error saving {var}: {e}")

            ds.close()

        except Exception as e:
            print(f"Error processing {nc_file.name}: {e}")

    print("\nLayer extraction finished.\n")


# -------------------------------------------------------
# Standalone execution
# -------------------------------------------------------

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Extract SWOT Raster layers"
    )

    parser.add_argument("--input", required=True,
                        help="Folder with SWOT NetCDF")

    parser.add_argument("--output", required=True,
                        help="Output directory")

    args = parser.parse_args()

    extract_layers(
        input_dir=args.input,
        output_dir=args.output
    )