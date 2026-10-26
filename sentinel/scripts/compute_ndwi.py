#!/usr/bin/env python3
"""
compute_ndwi.py
---------------
Computes the Normalized Difference Water Index (NDWI; McFeeters, 1996) and optional
Modified NDWI (MNDWI; Xu, 2006) from Sentinel-2 MSI Level-2A surface reflectance bands.

Formulas:
    NDWI  = (B03_Green - B08_NIR) / (B03_Green + B08_NIR)
    MNDWI = (B03_Green - B11_SWIR) / (B03_Green + B11_SWIR)

Outputs:
    GeoTIFF file containing the continuous water index values (-1.0 to +1.0).
"""

import argparse
from pathlib import Path
import numpy as np
import rasterio


def compute_spectral_index(b_green_path, b_nir_path, output_path, b_swir_path=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading Green band: {b_green_path}")
    with rasterio.open(b_green_path) as src_g:
        meta = src_g.meta.copy()
        green = src_g.read(1).astype(np.float32)

    print(f"Reading NIR band: {b_nir_path}")
    with rasterio.open(b_nir_path) as src_nir:
        nir = src_nir.read(1).astype(np.float32)

    # Compute NDWI
    numerator = green - nir
    denominator = green + nir
    with np.errstate(divide="ignore", invalid="ignore"):
        ndwi = np.where(denominator != 0, numerator / denominator, np.nan)

    # Clip to physical valid range [-1.0, 1.0]
    ndwi = np.clip(ndwi, -1.0, 1.0)

    # Save as GeoTIFF
    meta.update({
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "nodata": np.nan
    })

    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(ndwi, 1)

    print(f"NDWI raster successfully exported to: {output_path}")

    # Optionally compute MNDWI if SWIR band is provided
    if b_swir_path:
        mndwi_out = output_path.with_name(output_path.stem.replace("ndwi", "mndwi") + output_path.suffix)
        with rasterio.open(b_swir_path) as src_swir:
            swir = src_swir.read(1).astype(np.float32)
        num_m = green - swir
        den_m = green + swir
        with np.errstate(divide="ignore", invalid="ignore"):
            mndwi = np.where(den_m != 0, num_m / den_m, np.nan)
        mndwi = np.clip(mndwi, -1.0, 1.0)
        with rasterio.open(mndwi_out, "w", **meta) as dst:
            dst.write(mndwi, 1)
        print(f"MNDWI raster successfully exported to: {mndwi_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute NDWI / MNDWI from Sentinel-2 bands.")
    parser.add_argument("--green", required=True, help="Path to Sentinel-2 Band 3 (Green) GeoTIFF/JP2")
    parser.add_argument("--nir", required=True, help="Path to Sentinel-2 Band 8 (NIR) GeoTIFF/JP2")
    parser.add_argument("--output", required=True, help="Output destination GeoTIFF for NDWI")
    parser.add_argument("--swir", default=None, help="Optional Band 11 (SWIR) for MNDWI calculation")
    args = parser.parse_args()

    compute_spectral_index(args.green, args.nir, args.output, args.swir)
