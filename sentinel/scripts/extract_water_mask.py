#!/usr/bin/env python3
"""
extract_water_mask.py
---------------------
Thresholds continuous NDWI/MNDWI raster imagery into a discrete binary water mask:
- 1: Water body
- 0: Non-water / land

Applies optional morphological filtering (opening/closing) to remove isolated speckle
noise and residual cloud/shadow artifacts.

Outputs:
    Binary water mask GeoTIFF (uint8).
"""

import argparse
from pathlib import Path
import numpy as np
import rasterio

try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def threshold_water(ndwi_path, output_path, threshold=0.0, apply_morphology=False):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(ndwi_path) as src:
        meta = src.meta.copy()
        ndwi = src.read(1)

    # Thresholding: water typically displays positive NDWI values
    water_mask = np.where(ndwi > threshold, 1, 0).astype(np.uint8)

    # Preserve nodata areas from original input
    if src.nodata is not None and not np.isnan(src.nodata):
        water_mask[ndwi == src.nodata] = 0
    elif np.isnan(ndwi).any():
        water_mask[np.isnan(ndwi)] = 0

    # Optional morphological cleanup
    if apply_morphology and HAS_SCIPY:
        # 3x3 structuring element
        struct = ndimage.generate_binary_structure(2, 1)
        # Remove small isolated false positives (opening)
        water_mask = ndimage.binary_opening(water_mask, structure=struct).astype(np.uint8)
        # Fill small holes inside the reservoir body (closing)
        water_mask = ndimage.binary_closing(water_mask, structure=struct).astype(np.uint8)

    meta.update({
        "driver": "GTiff",
        "dtype": "uint8",
        "count": 1,
        "nodata": 0
    })

    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(water_mask, 1)

    total_water_pixels = int(np.sum(water_mask == 1))
    print(f"Binary water mask created: {output_path} (Water pixels: {total_water_pixels})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Threshold NDWI into binary water mask.")
    parser.add_argument("--ndwi", required=True, help="Path to continuous NDWI GeoTIFF")
    parser.add_argument("--output", required=True, help="Destination binary mask GeoTIFF")
    parser.add_argument("--threshold", type=float, default=0.0, help="NDWI water threshold (default: 0.0)")
    parser.add_argument("--filter", action="store_true", help="Apply morphological noise filtering")
    args = parser.parse_args()

    threshold_water(args.ndwi, args.output, args.threshold, args.filter)
