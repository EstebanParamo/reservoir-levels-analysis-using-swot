#!/usr/bin/env python3
"""
polygonize_and_area.py
----------------------
Converts binary water mask raster into vector polygons, isolates the main reservoir
body (replicating the QGIS workflow described in Section 3.3.4 of the thesis),
reprojects to the official Colombian coordinate system MAGNA-SIRGAS 2018 (EPSG:9377)
or UTM Zone 18N (EPSG:32618), and computes the exact water surface area (km²).

Outputs:
    - GeoPackage / Shapefile with the delineated reservoir water polygon
    - Summary CSV entry reporting acquisition date, area (m²), and area (km²)
"""

import argparse
from pathlib import Path
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import pandas as pd


def polygonize_and_calculate_area(mask_path, output_vector, output_csv=None,
                                   boundary_shape=None, target_crs="EPSG:9377",
                                   date_str=None, reservoir_name="reservoir"):
    mask_path = Path(mask_path)
    output_vector = Path(output_vector)
    output_vector.parent.mkdir(parents=True, exist_ok=True)

    print(f"Polygonizing water mask: {mask_path}")
    with rasterio.open(mask_path) as src:
        image = src.read(1)
        src_crs = src.crs
        transform = src.transform

    # Extract polygon geometries where pixel value is 1 (water)
    mask = (image == 1)
    results = (
        {"properties": {"raster_val": int(v)}, "geometry": s}
        for s, v in shapes(image, mask=mask, transform=transform)
    )

    geoms = [shape(r["geometry"]) for r in results]
    if not geoms:
        print("Warning: No water polygons detected in mask.")
        return 0.0

    gdf = gpd.GeoDataFrame({"geometry": geoms}, crs=src_crs)

    # Spatial filtering against reservoir boundary if provided
    if boundary_shape:
        print(f"Applying spatial boundary filter from: {boundary_shape}")
        boundary_gdf = gpd.read_file(boundary_shape)
        if boundary_gdf.crs != gdf.crs:
            boundary_gdf = boundary_gdf.to_crs(gdf.crs)
        # Spatial intersection
        gdf = gpd.overlay(gdf, boundary_gdf, how="intersection")
        if len(gdf) == 0:
            print("Warning: No overlapping water polygons within reservoir boundary.")
            return 0.0

    # Dissolve all remaining water polygons into a single entity
    dissolved = gdf.dissolve()

    # Reproject to metric system (MAGNA-SIRGAS 2018 / EPSG:9377 by default)
    dissolved_metric = dissolved.to_crs(target_crs)

    # Compute planar geometric area
    area_m2 = float(dissolved_metric.geometry.area.iloc[0])
    area_km2 = area_m2 / 1_000_000.0

    # Add attributes
    dissolved_metric["reservoir"] = reservoir_name
    dissolved_metric["date"] = date_str if date_str else "unknown"
    dissolved_metric["area_m2"] = area_m2
    dissolved_metric["area_km2"] = round(area_km2, 6)
    dissolved_metric["crs"] = target_crs

    # Export vector layer
    driver = "GPKG" if output_vector.suffix.lower() == ".gpkg" else "ESRI Shapefile"
    dissolved_metric.to_file(output_vector, driver=driver)
    print(f"Delineated water contour saved to: {output_vector}")
    print(f"Computed Surface Area: {area_km2:.4f} km² ({area_m2:,.2f} m²)")

    # Append to summary CSV
    if output_csv:
        output_csv = Path(output_csv)
        row_data = [{
            "date": date_str,
            "reservoir": reservoir_name,
            "area_km2": round(area_km2, 6),
            "area_m2": round(area_m2, 2),
            "source_file": mask_path.name
        }]
        df_new = pd.DataFrame(row_data)
        if output_csv.exists():
            df_existing = pd.read_csv(output_csv)
            df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=["date", "reservoir"])
            df_combined.to_csv(output_csv, index=False)
        else:
            df_new.to_csv(output_csv, index=False)
        print(f"Record appended to time series table: {output_csv}")

    return area_km2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polygonize water mask and compute surface area.")
    parser.add_argument("--mask", required=True, help="Path to binary water mask GeoTIFF")
    parser.add_argument("--output_vector", required=True, help="Output GeoPackage/Shapefile path")
    parser.add_argument("--output_csv", default=None, help="Path to append time series CSV record")
    parser.add_argument("--boundary", default=None, help="Optional reservoir boundary polygon for spatial clipping")
    parser.add_argument("--crs", default="EPSG:9377", help="Target metric CRS (default: EPSG:9377 MAGNA-SIRGAS)")
    parser.add_argument("--date", default=None, help="Acquisition date (YYYY-MM-DD)")
    parser.add_argument("--reservoir", default="reservoir", help="Reservoir name (chuza / san_rafael)")
    args = parser.parse_args()

    polygonize_and_calculate_area(
        args.mask, args.output_vector, args.output_csv,
        args.boundary, args.crs, args.date, args.reservoir
    )
