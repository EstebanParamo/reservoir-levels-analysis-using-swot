# -------------------------------------------------------
# clip.py
# Clip SWOT mosaics using reservoir shapefile
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import rasterio
from rasterio.mask import mask
from pathlib import Path
import geopandas as gpd


VARIABLES = ["wse", "area", "sig0"]


def ensure_dirs(base_dir):

    clipped_dir = base_dir / "clipped"

    dirs = {
        "wse": clipped_dir / "wse",
        "area": clipped_dir / "area",
        "sig0": clipped_dir / "sig0"
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    return dirs


def clip_mosaics(output_dir, shape_path):

    output_dir = Path(output_dir)

    mosaic_dir = output_dir / "mosaic"
    dirs = ensure_dirs(output_dir)

    print("\nLoading reservoir geometry...")
    gdf = gpd.read_file(shape_path)

    if len(gdf) == 0:
        raise ValueError("Shapefile has no geometries.")

    geometry = gdf.geometry.values

    for group in VARIABLES:

        print(f"\nProcessing {group.upper()} mosaics")

        files = list((mosaic_dir / group).glob("*.tif"))

        for f in files:

            out_name = f.name
            out_path = dirs[group] / out_name

            try:

                with rasterio.open(f) as src:

                    out_image, out_transform = mask(
                        src,
                        geometry,
                        crop=True
                    )

                    meta = src.meta.copy()

                    meta.update({
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                        "compress": "LZW"
                    })

                    with rasterio.open(out_path, "w", **meta) as dst:
                        dst.write(out_image)

                print(f"Clipped: {out_name}")

            except Exception as e:
                print(f"Error clipping {f.name}: {e}")

    print("\nClipping finished.\n")


# -------------------------------------------------------
# Standalone execution
# -------------------------------------------------------

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Clip SWOT mosaics using reservoir shapefile"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Results directory"
    )

    parser.add_argument(
        "--shape",
        required=True,
        help="Reservoir shapefile (.gpkg)"
    )

    args = parser.parse_args()

    clip_mosaics(
        output_dir=args.output,
        shape_path=args.shape
    )