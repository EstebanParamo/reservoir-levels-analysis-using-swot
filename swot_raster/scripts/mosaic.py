# -------------------------------------------------------
# mosaic.py
# Build mosaics from SWOT tiles (073F, 074F, etc.)
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import re
from pathlib import Path
import rasterio
from rasterio.merge import merge


VARIABLES = {
    "wse": "wse",
    "area": "water_area",
    "sig0": "sig0"
}


def parse_name(filename):
    """
    Extract variable, date and tile from filename.
    Example:
    wse_2023-12-17_073F.tif
    """

    match = re.match(r"(.*)_(\d{4}-\d{2}-\d{2})_(\d{3}F)\.tif", filename)

    if not match:
        return None, None, None

    var = match.group(1)
    date = match.group(2)
    tile = match.group(3)

    return var, date, tile


def group_tiles(files):
    """
    Group tiles by variable and date.
    """

    groups = {}

    for f in files:

        var, date, tile = parse_name(f.name)

        if var is None:
            continue

        key = (var, date)

        groups.setdefault(key, []).append(f)

    return groups


def ensure_dirs(base_dir):

    mosaic_dir = base_dir / "mosaic"

    dirs = {
        "wse": mosaic_dir / "wse",
        "area": mosaic_dir / "area",
        "sig0": mosaic_dir / "sig0"
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    return dirs


def build_mosaics(output_dir):

    output_dir = Path(output_dir)

    layers_dir = output_dir / "layers"
    dirs = ensure_dirs(output_dir)

    for group in ["wse", "area", "sig0"]:

        print(f"\nProcessing {group.upper()} mosaics")

        files = list((layers_dir / group).glob("*.tif"))

        groups = group_tiles(files)

        for (var, date), tiles in groups.items():

            out_name = f"{var}_{date}.tif"
            out_path = dirs[group] / out_name

            if len(tiles) == 1:

                # Only one tile
                src = rasterio.open(tiles[0])

                meta = src.meta.copy()

                with rasterio.open(out_path, "w", **meta) as dst:
                    dst.write(src.read())

                src.close()

                print(f"Mosaic (single tile): {out_name}")

            else:

                import rioxarray

                corrected_files = []

                for f in tiles:
                    try:
                        da = rioxarray.open_rasterio(f, masked=True)
                        da = da.rio.reproject(da.rio.crs)
                        fixed = f.with_name(f.stem + "_fixed.tif")
                        da.rio.to_raster(fixed)
                        corrected_files.append(fixed)
                    except Exception:
                        corrected_files.append(f)

                srcs = [rasterio.open(fp) for fp in corrected_files]

                mosaic, transform = merge(srcs)

                meta = srcs[0].meta.copy()

                meta.update({
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": transform,
                    "compress": "LZW"
                })

                with rasterio.open(out_path, "w", **meta) as dst:
                    dst.write(mosaic)

                for s in srcs:
                    s.close()

                print(f"Mosaic created: {out_name}")


# -------------------------------------------------------
# Standalone execution
# -------------------------------------------------------

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Build mosaics from SWOT tiles"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory (same used in extract_layers)"
    )

    args = parser.parse_args()

    build_mosaics(args.output)