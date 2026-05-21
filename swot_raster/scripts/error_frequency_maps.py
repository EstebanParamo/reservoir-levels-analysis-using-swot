# -------------------------------------------------------
# error_frequency_maps.py
# Compute spatial frequency of SWOT bitwise quality flags
# Also generates dominant error map
# Compatible: Windows / MacOS / Linux
# -------------------------------------------------------

import rasterio
import numpy as np
from pathlib import Path
import argparse
import re


FILL_VALUE = 4294967295


BIT_NAMES = {

    1: "dark_water",
    2: "low_coherence",
    12: "classification_degraded",
    14: "land_contamination",
    19: "geophysical_correction",
    20: "geophysical_model",
    21: "atmospheric_correction",
    26: "sig0_quality_degraded",
    28: "geolocation_uncertainty",
    29: "high_measurement_uncertainty"

}


def extract_date(name):

    m = re.search(r"\d{4}-\d{2}-\d{2}", name)

    if m:
        return m.group(0)

    return None


def detect_active_bits(files):

    bits = set()

    for f in files:

        with rasterio.open(f) as src:

            arr = src.read(1).astype("uint32")

            arr[arr == FILL_VALUE] = 0

        for b in range(32):

            if np.any(((arr >> b) & 1) == 1):
                bits.add(b)

    return sorted(bits)


def compute_frequency_maps(files, bits):

    with rasterio.open(files[0]) as src:

        meta = src.meta.copy()

        height = src.height
        width = src.width

    counts = {b: np.zeros((height, width), dtype=np.float32) for b in bits}

    n_scenes = len(files)

    for f in files:

        with rasterio.open(f) as src:

            arr = src.read(1).astype("uint32")

            arr[arr == FILL_VALUE] = 0

        for b in bits:

            mask = ((arr >> b) & 1)

            counts[b] += mask

    freq = {}

    for b in bits:

        freq[b] = (counts[b] / n_scenes) * 100

    return freq, meta


def compute_dominant_error(freq_maps):

    stack = np.stack(list(freq_maps.values()))

    dominant = np.argmax(stack, axis=0)

    bits = list(freq_maps.keys())

    dominant_bit = np.zeros_like(dominant)

    for i, b in enumerate(bits):

        dominant_bit[dominant == i] = b

    return dominant_bit


def process_variable(var_dir, out_dir):

    files = sorted([

        f for f in var_dir.glob("*.tif")

        if re.match(r".*_qual_bitwise_\d{4}-\d{2}-\d{2}\.tif$", f.name)

    ])

    if len(files) == 0:

        print("No bitwise files found")
        return

    print(f"{len(files)} scenes detected")

    bits = detect_active_bits(files)

    print("Active bits:", bits)

    freq_maps, meta = compute_frequency_maps(files, bits)

    meta.update(dtype="float32", count=1, nodata=None)

    for b, arr in freq_maps.items():

        name = BIT_NAMES.get(b, f"bit{b}")

        out = out_dir / f"{var_dir.name}_bit{b}_{name}_frequency.tif"

        with rasterio.open(out, "w", **meta) as dst:

            dst.write(arr.astype("float32"), 1)

    print("Frequency maps saved")

    dominant = compute_dominant_error(freq_maps)

    meta.update(dtype="uint8", nodata=0)

    out = out_dir / f"{var_dir.name}_dominant_error.tif"

    with rasterio.open(out, "w", **meta) as dst:

        dst.write(dominant.astype("uint8"), 1)

    print("Dominant error map saved")


def error_frequency_maps(output_dir):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped"

    maps_dir = output_dir / "maps" / "error_frequency"

    maps_dir.mkdir(parents=True, exist_ok=True)

    variables = {

        "wse": clipped_dir / "wse",
        "area": clipped_dir / "area",
        "sig0": clipped_dir / "sig0"

    }

    for var, var_dir in variables.items():

        print(f"\nProcessing {var}")

        out_dir = maps_dir / var

        out_dir.mkdir(exist_ok=True)

        process_variable(var_dir, out_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True,
        help="Results directory"
    )

    args = parser.parse_args()

    error_frequency_maps(args.output)