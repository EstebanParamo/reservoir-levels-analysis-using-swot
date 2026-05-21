import rasterio
import numpy as np
from pathlib import Path
import argparse
import re


def extract_date(name):

    m = re.search(r"\d{4}-\d{2}-\d{2}", name)

    if m:
        return m.group(0)

    return None


def decode_bit(arr, bit):

    return ((arr.astype(np.uint32) >> bit) & 1)


def compute_frequency(files, bit):

    stack = []

    for f in files:

        with rasterio.open(f) as src:

            arr = src.read(1)

            if src.nodata is not None:
                arr = arr.astype(float)
                arr[arr == src.nodata] = np.nan

        decoded = decode_bit(arr, bit)

        stack.append(decoded)

    stack = np.array(stack)

    freq = np.sum(stack, axis=0) / stack.shape[0] * 100

    return freq


def process_variable(var_dir, maps_dir):

    files = sorted(var_dir.glob("*bitwise*.tif"))

    if len(files) == 0:
        print("No bitwise files found")
        return

    print(f"{len(files)} scenes found")

    with rasterio.open(files[0]) as src:
        meta = src.meta.copy()

    meta.update(dtype="float32")

    for bit in range(32):

        freq = compute_frequency(files, bit)

        out_path = maps_dir / f"bit_{bit}_frequency.tif"

        with rasterio.open(out_path, "w", **meta) as dst:

            dst.write(freq.astype(np.float32), 1)

    print("Frequency maps created")


def spatial_diagnostics(output_dir):

    output_dir = Path(output_dir)

    clipped_dir = output_dir / "clipped"
    maps_dir = output_dir / "maps"

    maps_dir.mkdir(exist_ok=True)

    variables = ["wse", "area", "sig0"]

    for var in variables:

        print(f"\nProcessing {var}")

        var_dir = clipped_dir / var

        if not var_dir.exists():
            print("Directory not found")
            continue

        out_dir = maps_dir / var
        out_dir.mkdir(exist_ok=True)

        process_variable(var_dir, out_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    spatial_diagnostics(args.output)