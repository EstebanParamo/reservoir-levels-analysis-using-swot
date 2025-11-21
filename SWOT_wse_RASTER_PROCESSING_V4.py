import os
import re
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import rioxarray
from datetime import datetime
from pathlib import Path
import platform
import shutil
import argparse

# ---------- GLOBAL CONFIGURATION ----------
MIN_ELEV = 2900.0   # default minimum valid elevation for WSE (meters)
MAX_ELEV = 3200.0   # default maximum valid elevation for WSE (meters)


class SWOTRasterProcessor:
    """
    Processor for SWOT raster files to extract WSE, build mosaics, clip by a polygon,
    compute statistics (manual / percentile / std-based), plot results and clean large intermediates.
    """

    def __init__(self, input_dir, shapefile_path, output_dir):
        self.input_dir = str(input_dir)
        self.shapefile_path = str(shapefile_path)
        self.output_dir = str(output_dir)

        self.reservoir_name = os.path.splitext(os.path.basename(self.shapefile_path))[0]
        self.system_name = platform.system()

        # a local date stamp for this run (YYYY-MM-DD)
        self.run_date = datetime.now().strftime("%Y-%m-%d")

        # results main folder
        self.results_dir = os.path.join(self.output_dir, f"RESULTS_{self.reservoir_name}")
        os.makedirs(self.results_dir, exist_ok=True)

        # csv folder
        self.csv_dir = os.path.join(self.results_dir, "CSV")
        os.makedirs(self.csv_dir, exist_ok=True)

        # organized subfolders
        self.dirs = {
            "raw": self.input_dir,
            "shape": os.path.dirname(self.shapefile_path),
            "output": self.output_dir,
            "csv": self.csv_dir,
            "wse_tif": os.path.join(self.results_dir, "TIF"),
            "wse_mosaic": os.path.join(self.results_dir, "MOSAIC"),
            "wse_clipped": os.path.join(self.results_dir, "CLIPPED"),
            "plots": os.path.join(self.results_dir, "PLOTS"),
        }

        # create subfolders
        for p in self.dirs.values():
            os.makedirs(p, exist_ok=True)

        # load shapefile (raise if not found)
        if not os.path.exists(self.shapefile_path):
            raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")

        self.mask_gdf = gpd.read_file(self.shapefile_path)
        print(f"Processor initialized for: {self.reservoir_name} ({self.system_name})")

        # default runtime parameters (can be overridden)
        self.mode = "manual"
        self.percentiles = [5.0, 95.0]
        self.std_factor = 2.0
        self.min_cota = MIN_ELEV
        self.max_cota = MAX_ELEV

    # 1) extract WSE variable from NetCDF files and save as GeoTIFF
    def extract_wse_from_nc(self):
        print("Extracting WSE from .nc files...")
        nc_files = [f for f in os.listdir(self.dirs["raw"]) if f.endswith(".nc")]
        records = []

        for fn in nc_files:
            src_path = os.path.join(self.dirs["raw"], fn)
            try:
                ds = xr.open_dataset(src_path)

                if "wse" not in ds:
                    print(f"Warning: 'wse' variable not found in {fn}")
                    continue

                wse = ds["wse"]
                mean_wse = round(float(np.nanmean(wse.values)), 4)

                # date parsing from filename (pattern _YYYYMMDDT)
                m = re.search(r"_(\d{8})T", fn)
                date_str = m.group(1) if m else "00000000"
                date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

                parts = fn.split("_")
                orbit = parts[8] if len(parts) > 8 else "NA"
                scene = parts[9] if len(parts) > 9 else "NA"

                tif_path = os.path.join(self.dirs["wse_tif"], fn.replace(".nc", "_wse.tif"))

                try:
                    # assign CRS if needed and export to GeoTIFF (EPSG:32618 forced here)
                    wse.rio.write_crs("EPSG:32618", inplace=True)
                    wse.rio.to_raster(tif_path, compress="LZW")
                except Exception as write_err:
                    print(f"Warning exporting {fn} (CRS/write error): {write_err}")
                    continue

                records.append({
                    "date": date_fmt,
                    "orbit": orbit,
                    "scene": scene,
                    "wse_mean": mean_wse,
                    "nc_file": fn,
                    "tif_path": tif_path
                })

                print(f"{fn}: mean WSE = {mean_wse}")

            except Exception as e:
                print(f"Warning processing {fn}: {e}")

        if records:
            df = pd.DataFrame(records)
            csv_out = os.path.join(self.dirs["csv"], "wse_extraction.csv")
            df.to_csv(csv_out, index=False)
            print(f"WSE extraction CSV written: {csv_out}")
        else:
            print("No valid extraction records generated.")

    # 2) create mosaics by date (try to correct orientation with rioxarray)
    def mosaic_scenes(self):
        print("Building mosaics...")
        tif_dir = self.dirs["wse_tif"]
        mosaic_dir = self.dirs["wse_mosaic"]
        all_tifs = [os.path.join(tif_dir, f) for f in os.listdir(tif_dir) if f.endswith("_wse.tif")]

        # group by date extracted from filename
        date_dict = {}
        for p in all_tifs:
            name = os.path.basename(p)
            match = re.search(r"_(\d{8})T", name)
            if match:
                date_key = datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")
                date_dict.setdefault(date_key, []).append(p)

        mosaic_records = []

        for date_key, tif_list in date_dict.items():
            print(f"Processing date {date_key} ({len(tif_list)} scenes)...")
            corrected = []

            for f in tif_list:
                try:
                    da = rioxarray.open_rasterio(f, masked=True)
                    da = da.rio.reproject(da.rio.crs)
                    fixed = f.replace(".tif", "_fixed.tif")
                    da.rio.to_raster(fixed)
                    corrected.append(fixed)
                except Exception as e:
                    print(f"Warning correcting orientation for {os.path.basename(f)}: {e}")
                    corrected.append(f)

            if len(corrected) == 1:
                src_path = corrected[0]
                dst_path = os.path.join(mosaic_dir, f"mosaic_{date_key}.tif")
                with rasterio.open(src_path) as src:
                    meta = src.meta.copy()
                    data = src.read(1)
                    meta.update(compress="LZW")
                    with rasterio.open(dst_path, "w", **meta) as dst:
                        dst.write(data, 1)
                print(f"Single-scene mosaic copied: {dst_path}")
                mosaic_records.append({"date": date_key, "mosaic_path": dst_path})
                continue

            try:
                srcs = [rasterio.open(fp) for fp in corrected]
                mosaic_arr, out_trans = merge(srcs)
                out_meta = srcs[0].meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": mosaic_arr.shape[1],
                    "width": mosaic_arr.shape[2],
                    "transform": out_trans,
                    "compress": "LZW"
                })

                out_path = os.path.join(mosaic_dir, f"mosaic_{date_key}.tif")
                with rasterio.open(out_path, "w", **out_meta) as dst:
                    dst.write(mosaic_arr)
                print(f"Mosaic created: {os.path.basename(out_path)}")
                mosaic_records.append({"date": date_key, "mosaic_path": out_path})

            except Exception as e:
                print(f"Warning: could not merge mosaics for {date_key}. Saving scenes individually. Error: {e}")
                for fixed in corrected:
                    dest_single = os.path.join(mosaic_dir, os.path.basename(fixed))
                    try:
                        shutil.copy2(fixed, dest_single)
                        mosaic_records.append({"date": date_key, "mosaic_path": dest_single})
                    except Exception as ce:
                        print(f"Warning copying corrected file {fixed}: {ce}")
            finally:
                for s in locals().get("srcs", []):
                    try:
                        s.close()
                    except Exception:
                        pass

        if mosaic_records:
            df_out = pd.DataFrame(mosaic_records)
            csv_out = os.path.join(self.dirs["csv"], "wse_mosaic.csv")
            df_out.to_csv(csv_out, index=False)
            print(f"Mosaics CSV written: {csv_out}")
        else:
            print("No valid mosaics generated.")

    # 3) clip mosaics using the supplied shapefile and compute per-clip mean (rounded)
    def clip_with_shape(self):
        print("Clipping mosaics with shape...")
        mosaic_csv = os.path.join(self.dirs["csv"], "wse_mosaic.csv")
        if not os.path.exists(mosaic_csv) or os.path.getsize(mosaic_csv) == 0:
            print("No mosaic CSV found; skipping clipping.")
            return

        df = pd.read_csv(mosaic_csv)
        if df.empty or "mosaic_path" not in df.columns:
            print("Mosaic CSV empty or missing 'mosaic_path' column.")
            return

        gdf = gpd.read_file(self.shapefile_path)
        clipped_records = []

        for _, row in df.iterrows():
            in_path = row["mosaic_path"]
            if not os.path.exists(in_path):
                continue

            out_path = os.path.join(self.dirs["wse_clipped"], f"CLIP_{os.path.basename(in_path)}")
            try:
                with rasterio.open(in_path) as src:
                    out_image, out_transform = mask(src, gdf.geometry, crop=True)
                    out_meta = src.meta.copy()
                    out_meta.update({
                        "driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                        "compress": "LZW"
                    })

                    with rasterio.open(out_path, "w", **out_meta) as dst:
                        dst.write(out_image)

                    arr = out_image.astype(float)
                    if src.nodata is not None:
                        arr[arr == src.nodata] = np.nan

                    if np.all(np.isnan(arr)):
                        mean_val = np.nan
                    else:
                        mean_val = round(float(np.nanmean(arr)), 4)

                    clipped_records.append({
                        "date": row["date"],
                        "clip_path": out_path,
                        "wse_mean": mean_val
                    })

                    print(f"Clipped: {os.path.basename(out_path)} | mean WSE: {mean_val}")

            except Exception as e:
                print(f"Error clipping {in_path}: {e}")

        if clipped_records:
            df_out = pd.DataFrame(clipped_records)
            csv_out = os.path.join(self.dirs["csv"], "wse_clipped.csv")
            df_out.to_csv(csv_out, index=False)
            print(f"Clipped records CSV written: {csv_out}")
        else:
            print("No clipped results generated.")

    # Helper: compute stats for a single array given a method
    def _compute_stats_from_array(self, data, method, min_manual, max_manual, p_low, p_high, std_factor):
        """
        Returns (min_val, max_val, mean, min, max, std, meta_info)
        meta_info is a small string used for titles/legend (percentiles/std factor)
        """
        # flatten nan-aware
        arr = data.copy().astype(float)
        arr[np.isinf(arr)] = np.nan

        if method == "manual":
            min_val = min_manual
            max_val = max_manual
            mask_valid = (arr >= min_val) & (arr <= max_val)
            meta = f"manual {min_val:.2f}–{max_val:.2f} m"
        elif method == "auto_percentil":
            # use nanpercentile excluding nans
            try:
                p_low_val, p_high_val = np.nanpercentile(arr, [p_low, p_high])
            except Exception:
                # fallback if array is all nans or degenerate
                p_low_val, p_high_val = (np.nan, np.nan)
            min_val, max_val = p_low_val, p_high_val
            mask_valid = (arr >= min_val) & (arr <= max_val)
            meta = f"percentiles {p_low:.0f}-{p_high:.0f} ({min_val:.2f}–{max_val:.2f} m)"
        elif method == "auto_std":
            mean_all = np.nanmean(arr)
            std_all = np.nanstd(arr)
            min_val = mean_all - std_factor * std_all
            max_val = mean_all + std_factor * std_all
            mask_valid = (arr >= min_val) & (arr <= max_val)
            meta = f"mean±{std_factor:.2f}σ ({min_val:.2f}–{max_val:.2f} m)"
        else:
            raise ValueError(f"Unknown method: {method}")

        filtered = np.where(mask_valid, arr, np.nan)

        if np.isnan(filtered).all():
            return None, None, np.nan, np.nan, np.nan, np.nan, meta

        mean_v = float(np.nanmean(filtered))
        min_v = float(np.nanmin(filtered))
        max_v = float(np.nanmax(filtered))
        std_v = float(np.nanstd(filtered))

        return min_val, max_val, round(mean_v, 4), round(min_v, 4), round(max_v, 4), round(std_v, 4), meta

    # 4) compute means and statistics supporting manual / percentile / std modes (and 'all')
    def calculate_mean(self):
        """
        Compute WSE statistics using manual, percentile-based, std-based, or run all methods and build CSVs.
        """
        mode = getattr(self, "mode", "manual")
        p_low, p_high = getattr(self, "percentiles", [5.0, 95.0])
        std_factor = getattr(self, "std_factor", 2.0)
        min_manual = getattr(self, "min_cota", MIN_ELEV)
        max_manual = getattr(self, "max_cota", MAX_ELEV)

        # Allowed methods and their order
        methods_order = ["manual", "auto_percentil", "auto_std"]

        # When mode == 'all' we will run all three
        run_methods = methods_order if mode == "all" else [mode]

        print(f"\nCalculating statistics. Mode: {mode}. Methods to run: {run_methods}")

        clipped_csv = os.path.join(self.dirs["csv"], "wse_clipped.csv")
        if not os.path.exists(clipped_csv) or os.path.getsize(clipped_csv) == 0:
            print("No clipped CSV found; skipping statistics.")
            return

        df = pd.read_csv(clipped_csv)
        if df.empty or "clip_path" not in df.columns:
            print("Clipped CSV empty or missing 'clip_path'.")
            return

        # We'll build per-method results (dictionary method -> list of dicts)
        per_method_results = {m: [] for m in run_methods}

        for _, row in df.iterrows():
            clip_path = row["clip_path"]
            if not os.path.exists(clip_path):
                continue

            try:
                with rasterio.open(clip_path) as src:
                    data = src.read(1).astype(float)
                    if src.nodata is not None:
                        data[data == src.nodata] = np.nan

                    for method in run_methods:
                        try:
                            min_v, max_v, mean_v, minv_v, maxv_v, std_v, meta = self._compute_stats_from_array(
                                data,
                                method,
                                min_manual,
                                max_manual,
                                p_low,
                                p_high,
                                std_factor
                            )
                        except ValueError as ve:
                            print(f"Error: {ve}")
                            continue

                        if np.isnan(mean_v):
                            # nothing valid for this method on this clip
                            print(f"No valid pixels for {os.path.basename(clip_path)} using method {method}")
                            # still append row with NaNs so dates remain aligned
                            per_method_results[method].append({
                                "date": row["date"],
                                "file": os.path.basename(clip_path),
                                "mean_wse": np.nan,
                                "min_wse": np.nan,
                                "max_wse": np.nan,
                                "std_wse": np.nan,
                                "meta": meta
                            })
                            continue

                        per_method_results[method].append({
                            "date": row["date"],
                            "file": os.path.basename(clip_path),
                            "mean_wse": mean_v,
                            "min_wse": minv_v,
                            "max_wse": maxv_v,
                            "std_wse": std_v,
                            "meta": meta
                        })

                        print(f"{os.path.basename(clip_path)} | method {method} | mean: {mean_v:.2f} | min: {minv_v:.2f} | max: {maxv_v:.2f} | std: {std_v:.2f}")

            except Exception as e:
                print(f"Error reading {clip_path}: {e}")

        # Save per-method CSVs and, if mode == 'all', write combined CSV
        for method, records in per_method_results.items():
            if not records:
                print(f"No results for method {method}, skipping CSV for it.")
                continue
            df_method = pd.DataFrame(records)
            csv_out = os.path.join(self.dirs["csv"], f"wse_stats_{method}.csv")
            df_method.to_csv(csv_out, index=False)
            print(f"Statistics CSV for method '{method}' written: {csv_out}")

        # If we ran more than one method, produce a combined csv with columns for each method
        if len(run_methods) > 1:
            merged = None
            for method in run_methods:
                csv_path = os.path.join(self.dirs["csv"], f"wse_stats_{method}.csv")
                if not os.path.exists(csv_path):
                    continue
                df_m = pd.read_csv(csv_path)
                # rename stats columns with method suffix
                rename_map = {
                    "mean_wse": f"mean_wse_{method}",
                    "min_wse": f"min_wse_{method}",
                    "max_wse": f"max_wse_{method}",
                    "std_wse": f"std_wse_{method}",
                    "meta": f"meta_{method}"
                }
                df_m_ren = df_m.rename(columns=rename_map)
                # keep date and file for merging
                if merged is None:
                    merged = df_m_ren
                else:
                    merged = pd.merge(merged, df_m_ren, on=["date", "file"], how="outer")

            if merged is not None:
                combined_csv = os.path.join(self.dirs["csv"], f"wse_stats_combined.csv")
                merged.to_csv(combined_csv, index=False)
                print(f"Combined statistics CSV written: {combined_csv}")
            else:
                print("No method CSVs found to build combined CSV.")

    # 5) plotting: per-method and combined plots (date-stamped run folder + per-method subfolders)
    def plot_results(self):
        print("Plotting results...")

        # create run plots folder (date-stamped)
        run_plots_dir = os.path.join(self.dirs["plots"], self.run_date)
        os.makedirs(run_plots_dir, exist_ok=True)

        # paths for per-method csvs
        method_files = {
            "manual": os.path.join(self.dirs["csv"], "wse_stats_manual.csv"),
            "auto_percentil": os.path.join(self.dirs["csv"], "wse_stats_auto_percentil.csv"),
            "auto_std": os.path.join(self.dirs["csv"], "wse_stats_auto_std.csv"),
        }
        combined_csv = os.path.join(self.dirs["csv"], "wse_stats_combined.csv")

        # Colors per method (consistent)
        colors = {
            "manual": "#1f77b4",         # blue
            "auto_percentil": "#ff7f0e", # orange
            "auto_std": "#2ca02c"        # green
        }

        # Read dataFrames per method if available (prefer per-method CSVs)
        dfs = {}
        metas = {}
        for method, path in method_files.items():
            if os.path.exists(path):
                dfm = pd.read_csv(path)
                if not dfm.empty:
                    dfm["date"] = pd.to_datetime(dfm["date"], errors="coerce")
                    dfm = dfm.sort_values("date")
                    dfs[method] = dfm
                    metas[method] = dfm["meta"].iloc[0] if "meta" in dfm.columns and not dfm["meta"].empty else ""

        # If combined exists and no per-method, extract columns
        if not dfs and os.path.exists(combined_csv):
            dfc = pd.read_csv(combined_csv)
            if not dfc.empty:
                dfc["date"] = pd.to_datetime(dfc["date"], errors="coerce")
                dfc = dfc.sort_values("date")
                for method in ["manual", "auto_percentil", "auto_std"]:
                    mean_col = f"mean_wse_{method}"
                    if mean_col in dfc.columns:
                        cols = ["date", "file", mean_col, f"min_wse_{method}", f"max_wse_{method}", f"std_wse_{method}", f"meta_{method}"]
                        cols_existing = [c for c in cols if c in dfc.columns]
                        dfi = dfc[cols_existing].copy()
                        rename_map = {}
                        if mean_col in dfi.columns:
                            rename_map[mean_col] = "mean_wse"
                        if f"min_wse_{method}" in dfi.columns:
                            rename_map[f"min_wse_{method}"] = "min_wse"
                        if f"max_wse_{method}" in dfi.columns:
                            rename_map[f"max_wse_{method}"] = "max_wse"
                        if f"std_wse_{method}" in dfi.columns:
                            rename_map[f"std_wse_{method}"] = "std_wse"
                        if f"meta_{method}" in dfi.columns:
                            rename_map[f"meta_{method}"] = "meta"
                        dfi = dfi.rename(columns=rename_map)
                        dfs[method] = dfi
                        metas[method] = dfi["meta"].iloc[0] if "meta" in dfi.columns and not dfi["meta"].empty else ""

        if not dfs:
            print("No statistics CSVs found for plotting; skipping plotting.")
            return

        # Prepare common date index union
        all_dates = pd.Index([]).astype('datetime64[ns]')
        for dfm in dfs.values():
            all_dates = all_dates.union(dfm["date"].dropna().unique())

        all_dates = np.sort(all_dates)

        # Create aggregated series per method (mean values per date)
        series = {}
        ranges = {}
        stds = {}
        for method, dfm in dfs.items():
            # compute daily mean across files (if multiple files per date exist)
            df_daily = dfm.groupby("date").agg({
                "mean_wse": "mean",
                "min_wse": "mean",
                "max_wse": "mean",
                "std_wse": "mean"
            }).reindex(all_dates)
            series[method] = df_daily["mean_wse"]
            ranges[method] = (df_daily["min_wse"], df_daily["max_wse"])
            stds[method] = df_daily["std_wse"]

        # ---------------------------
        # Per-method plots (3 per method)
        # ---------------------------
        for method, ser in series.items():
            method_folder = os.path.join(run_plots_dir, method)
            os.makedirs(method_folder, exist_ok=True)
            meta_text = metas.get(method, "")

            # a) Lines only
            plt.figure(figsize=(12, 6))
            plt.plot(all_dates, ser, marker="o", linestyle="-", label=f"{method} mean ({meta_text})", color=colors.get(method))
            title = f"Technical WSE Time Series — {self.reservoir_name} ({method} — lines only)"
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("WSE (m)")
            plt.legend()
            plt.grid(True)
            out_lines = os.path.join(method_folder, f"{self.reservoir_name}_{method}_LINES_{self.run_date}.png")
            plt.savefig(out_lines, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Plot saved: {out_lines}")

            # b) Std bands
            plt.figure(figsize=(12, 6))
            std_ser = stds.get(method)
            if std_ser is not None:
                upper = ser + std_ser
                lower = ser - std_ser
                plt.plot(all_dates, ser, marker="o", linestyle="-", color=colors.get(method), label=f"{method} mean")
                plt.fill_between(all_dates, lower, upper, alpha=0.2, label=f"{method} ± std ({meta_text})", color=colors.get(method))
            else:
                plt.plot(all_dates, ser, marker="o", linestyle="-", color=colors.get(method), label=f"{method} mean")
            title = f"Technical WSE Time Series — {self.reservoir_name} ({method} — std bands)"
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("WSE (m)")
            plt.legend()
            plt.grid(True)
            out_std = os.path.join(method_folder, f"{self.reservoir_name}_{method}_STD_BANDS_{self.run_date}.png")
            plt.savefig(out_std, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Plot saved: {out_std}")

            # c) Min-max range bands
            plt.figure(figsize=(12, 6))
            lo, hi = ranges.get(method, (None, None))
            plt.plot(all_dates, ser, marker="o", linestyle="-", color=colors.get(method), label=f"{method} mean")
            if lo is not None and hi is not None:
                plt.fill_between(all_dates, lo, hi, alpha=0.2, label=f"{method} min-max ({meta_text})", color=colors.get(method))
            title = f"Technical WSE Time Series — {self.reservoir_name} ({method} — min-max bands)"
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("WSE (m)")
            plt.legend()
            plt.grid(True)
            out_range = os.path.join(method_folder, f"{self.reservoir_name}_{method}_RANGE_BANDS_{self.run_date}.png")
            plt.savefig(out_range, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Plot saved: {out_range}")

        # ---------------------------
        # Combined plots (only if more than one method present)
        # ---------------------------
        if len(series) > 1:
            # 1) Combined lines
            plt.figure(figsize=(12, 6))
            for method, ser in series.items():
                plt.plot(all_dates, ser, marker="o", linestyle="-", label=f"{method} ({metas.get(method,'')})", color=colors.get(method))
            title = f"Technical WSE Time Series Comparison — {self.reservoir_name} (lines only)"
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("WSE (m)")
            plt.legend()
            plt.grid(True)
            out_lines_comb = os.path.join(run_plots_dir, f"{self.reservoir_name}_WSE_COMPARISON_LINES_{self.run_date}.png")
            plt.savefig(out_lines_comb, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Plot saved: {out_lines_comb}")

            # 2) Combined std bands
            plt.figure(figsize=(12, 6))
            for method, ser in series.items():
                std_ser = stds.get(method)
                if std_ser is not None:
                    upper = ser + std_ser
                    lower = ser - std_ser
                    plt.plot(all_dates, ser, marker="o", linestyle="-", color=colors.get(method), label=f"{method} mean")
                    plt.fill_between(all_dates, lower, upper, alpha=0.12, label=f"{method} ± std ({metas.get(method,'')})", color=colors.get(method))
                else:
                    plt.plot(all_dates, ser, marker="o", linestyle="-", color=colors.get(method), label=f"{method} mean")
            title = f"Technical WSE Time Series — {self.reservoir_name} (std bands)"
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("WSE (m)")
            plt.legend()
            plt.grid(True)
            out_std_comb = os.path.join(run_plots_dir, f"{self.reservoir_name}_WSE_STD_BANDS_{self.run_date}.png")
            plt.savefig(out_std_comb, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Plot saved: {out_std_comb}")

            # 3) Combined min-max range bands
            plt.figure(figsize=(12, 6))
            for method, ser in series.items():
                lo, hi = ranges.get(method, (None, None))
                plt.plot(all_dates, ser, marker="o", linestyle="-", color=colors.get(method), label=f"{method} mean")
                if lo is not None and hi is not None:
                    plt.fill_between(all_dates, lo, hi, alpha=0.12, label=f"{method} min-max ({metas.get(method,'')})", color=colors.get(method))
            title = f"Technical WSE Time Series — {self.reservoir_name} (min-max bands)"
            plt.title(title)
            plt.xlabel("Date")
            plt.ylabel("WSE (m)")
            plt.legend()
            plt.grid(True)
            out_range_comb = os.path.join(run_plots_dir, f"{self.reservoir_name}_WSE_RANGE_BANDS_{self.run_date}.png")
            plt.savefig(out_range_comb, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Plot saved: {out_range_comb}")

    # 6) clean large intermediate folders
    def cleanup_large_folders(self):
        print("Cleaning intermediate folders...")
        for folder in [self.dirs["wse_tif"], self.dirs["wse_mosaic"]]:
            try:
                shutil.rmtree(folder)
                print(f"Removed folder: {folder}")
            except Exception as e:
                print(f"Could not remove {folder}: {e}")

    # 7) run all steps
    def run_all(self):
        print(f"Starting full processing for {self.reservoir_name}")
        self.extract_wse_from_nc()
        self.mosaic_scenes()
        self.clip_with_shape()
        self.calculate_mean()
        self.plot_results()
        self.cleanup_large_folders()
        print(f"Processing completed for {self.reservoir_name}")


# MAIN EXECUTION
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process SWOT raster data to extract, mosaic, clip, and analyze WSE values."
    )
    parser.add_argument("--input", required=True, help="Path to the folder containing .nc files.")
    parser.add_argument("--shape", required=True, help="Path to the shapefile (.shp or .gpkg) used for clipping.")
    parser.add_argument("--output", required=True, help="Path to the folder where results will be stored.")
    parser.add_argument("--min", type=float, default=None, help="Minimum valid elevation (meters) for manual mode.")
    parser.add_argument("--max", type=float, default=None, help="Maximum valid elevation (meters) for manual mode.")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["manual", "auto_percentil", "auto_std", "all"],
        default="manual",
        help="Mode for filtering elevation data: 'manual', 'auto_percentil', 'auto_std', or 'all'."
    )
    parser.add_argument(
        "--percentiles",
        nargs=2,
        type=float,
        default=[5.0, 95.0],
        metavar=("LOW", "HIGH"),
        help="Percentile bounds used when mode='auto_percentil' (default: 5 95)."
    )
    parser.add_argument(
        "--std_factor",
        type=float,
        default=2.0,
        help="Standard deviation factor for mode='auto_std' (default: 2.0)."
    )

    args = parser.parse_args()

    processor = SWOTRasterProcessor(
        input_dir=args.input,
        shapefile_path=args.shape,
        output_dir=args.output
    )

    # Apply user parameters
    processor.mode = args.mode
    processor.percentiles = args.percentiles
    processor.std_factor = args.std_factor

    if args.min is not None and args.max is not None:
        processor.min_cota = args.min
        processor.max_cota = args.max
        print(f"Applied manual limits: {args.min}–{args.max} m")
    else:
        # keep defaults but show them
        print(f"Using manual defaults: {processor.min_cota}–{processor.max_cota} m")

    print(f"Selected mode: {processor.mode}")
    if processor.mode == "auto_percentil":
        print(f"Percentiles: {processor.percentiles[0]} - {processor.percentiles[1]}")
    if processor.mode == "auto_std":
        print(f"Std factor: {processor.std_factor}")

    processor.run_all()

