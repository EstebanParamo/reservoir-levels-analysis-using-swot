#!/usr/bin/env python3
"""
extract_lake_attributes.py
--------------------------
Extracts hydrological, uncertainty, and quality attributes for target lakes/reservoirs
from raw SWOT L2_HR_LakeSP shapefiles (either standalone .shp or packed inside .zip granules).

Outputs:
    A consolidated CSV containing all extracted passes and attributes for each reservoir.
"""

import argparse
import os
import re
import zipfile
from pathlib import Path
import pandas as pd

# Optional geopandas for spatial handling; fallback to dbfread / pyshp / struct if needed
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False


RESERVOIR_KEYWORDS = {
    "chuza": ["chuza", "chingaza"],
    "san_rafael": ["san rafael", "san_rafael"]
}

KEY_COLUMNS = [
    "lake_id", "reach_id", "obs_id", "time", "time_str",
    "wse", "wse_u", "wse_r_u", "wse_std",
    "area_total", "area_tot_u", "area_detct", "area_det_u",
    "layovr_val", "quality_f", "qual_f_b", "dark_frac",
    "lake_name", "p_storage", "p_ref_wse", "p_ref_area"
]


def extract_from_shapefile(shp_path, target_keywords=None):
    """Reads a shapefile using geopandas and filters records matching target keywords."""
    if not HAS_GEOPANDAS:
        raise RuntimeError("geopandas is required to process uncompressed shapefiles.")

    gdf = gpd.read_file(shp_path)
    if "lake_name" not in gdf.columns:
        return []

    records = []
    for _, row in gdf.iterrows():
        lake_name = str(row.get("lake_name", "")).strip()
        matched_target = None
        
        if target_keywords:
            lake_name_lower = lake_name.lower()
            for target_id, keywords in target_keywords.items():
                if any(kw in lake_name_lower for kw in keywords):
                    matched_target = target_id
                    break
        else:
            matched_target = lake_name

        if matched_target:
            rec = {col: row[col] if col in gdf.columns else None for col in KEY_COLUMNS}
            rec["target_reservoir"] = matched_target
            rec["source_file"] = Path(shp_path).name
            records.append(rec)

    return records


def extract_from_zip(zip_path, target_keywords=None):
    """Extracts target records directly from inside a SWOT LakeSP ZIP file."""
    if HAS_GEOPANDAS:
        # Use vsizip virtual file system
        vsi_path = f"/vsizip/{os.path.abspath(zip_path)}"
        try:
            with zipfile.ZipFile(zip_path) as z:
                shp_names = [f for f in z.namelist() if f.endswith(".shp")]
            
            all_records = []
            for shp_name in shp_names:
                full_vsi = f"{vsi_path}/{shp_name}"
                gdf = gpd.read_file(full_vsi)
                if "lake_name" not in gdf.columns:
                    continue
                for _, row in gdf.iterrows():
                    lake_name = str(row.get("lake_name", "")).strip()
                    matched_target = None
                    if target_keywords:
                        lake_name_lower = lake_name.lower()
                        for target_id, keywords in target_keywords.items():
                            if any(kw in lake_name_lower for kw in keywords):
                                matched_target = target_id
                                break
                    else:
                        matched_target = lake_name

                    if matched_target:
                        rec = {col: row[col] if col in gdf.columns else None for col in KEY_COLUMNS}
                        rec["target_reservoir"] = matched_target
                        rec["source_file"] = Path(zip_path).name
                        all_records.append(rec)
            return all_records
        except Exception as e:
            print(f"Warning reading {zip_path} via vsizip: {e}. Falling back to internal DBF parser.")

    # Fallback parsing directly from DBF inside ZIP (pure Python standard library)
    import struct
    records = []
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.endswith(".dbf"):
                with z.open(name) as dbf:
                    header = dbf.read(32)
                    num_records, header_len, record_len = struct.unpack("<IHH", header[4:12])
                    num_fields = (header_len - 33) // 32
                    fields = []
                    for _ in range(num_fields):
                        field_desc = dbf.read(32)
                        field_name = field_desc[:11].replace(b"\x00", b"").decode("ascii").strip()
                        field_len = field_desc[16]
                        fields.append((field_name, field_len))

                    dbf.seek(header_len)
                    for _ in range(num_records):
                        rec_bytes = dbf.read(record_len)
                        if not rec_bytes or rec_bytes[0:1] == b"*":
                            continue
                        offset = 1
                        val_dict = {}
                        for fn, flen in fields:
                            val = rec_bytes[offset:offset+flen].decode("utf-8", errors="ignore").strip()
                            offset += flen
                            val_dict[fn] = val

                        lake_name = val_dict.get("lake_name", "")
                        lake_name_lower = lake_name.lower()
                        matched_target = None
                        if target_keywords:
                            for target_id, keywords in target_keywords.items():
                                if any(kw in lake_name_lower for kw in keywords):
                                    matched_target = target_id
                                    break
                        else:
                            matched_target = lake_name

                        if matched_target:
                            rec = {col: val_dict.get(col, None) for col in KEY_COLUMNS}
                            rec["target_reservoir"] = matched_target
                            rec["source_file"] = Path(zip_path).name
                            records.append(rec)
    return records


def process_lakesp_directory(input_dir, output_dir, target=None):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    target_keywords = RESERVOIR_KEYWORDS
    if target:
        target_norm = target.lower().replace(" ", "_")
        if target_norm in RESERVOIR_KEYWORDS:
            target_keywords = {target_norm: RESERVOIR_KEYWORDS[target_norm]}
        else:
            target_keywords = {target_norm: [target.lower()]}

    all_records = []

    # Search for .zip granules
    zip_files = sorted(list(input_path.rglob("*.zip")))
    print(f"Found {len(zip_files)} .zip granules in {input_path}")
    for zf in zip_files:
        try:
            recs = extract_from_zip(zf, target_keywords)
            all_records.extend(recs)
        except Exception as e:
            print(f"Error processing {zf.name}: {e}")

    # Search for loose .shp files
    shp_files = sorted(list(input_path.rglob("*.shp")))
    print(f"Found {len(shp_files)} uncompressed .shp files in {input_path}")
    for sf in shp_files:
        try:
            recs = extract_from_shapefile(sf, target_keywords)
            all_records.extend(recs)
        except Exception as e:
            print(f"Error processing {sf.name}: {e}")

    if not all_records:
        print("No matching reservoir records found.")
        return

    df = pd.DataFrame(all_records)

    # Cast numeric columns
    numeric_cols = ["wse", "wse_u", "wse_r_u", "wse_std", "area_total", "area_tot_u",
                    "area_detct", "area_det_u", "quality_f", "qual_f_b", "dark_frac"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Format timestamp
    if "time_str" in df.columns:
        df["date"] = df["time_str"].str.slice(0, 10)
        df = df.sort_values(by=["target_reservoir", "date"]).reset_index(drop=True)

    # Save consolidated CSV
    out_file = output_path / "lakesp_extracted_raw.csv"
    df.to_csv(out_file, index=False)
    print(f"Extracted {len(df)} records saved to: {out_file}")

    # Also save per reservoir
    for reservoir, sub_df in df.groupby("target_reservoir"):
        res_file = output_path / f"lakesp_{reservoir}_raw.csv"
        sub_df.to_csv(res_file, index=False)
        print(f"Saved {len(sub_df)} records for {reservoir} to: {res_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract attributes from SWOT LakeSP shapefiles/zips.")
    parser.add_argument("--input", required=True, help="Folder containing SWOT LakeSP .zip or .shp files")
    parser.add_argument("--output", required=True, help="Output folder to store extracted CSVs")
    parser.add_argument("--target", default=None, help="Target reservoir filter (e.g., chuza, san_rafael)")
    args = parser.parse_args()

    process_lakesp_directory(args.input, args.output, args.target)
