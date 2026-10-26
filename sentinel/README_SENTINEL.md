# Subproject: Sentinel-2 Optical MSI Water Surface Area Extraction

This subfolder contains the optical remote sensing pipeline developed to delineate surface water extent and extract water surface area time series from **Sentinel-2 MultiSpectral Instrument (MSI) Level-2A** surface reflectance imagery.

This workflow serves as the independent optical benchmark used to cross-validate dynamic surface water area estimates against SWOT LakeSP and SWOT Raster observations over the **Chuza** and **San Rafael** reservoirs.

---

## Methodological Background

Due to high cloud frequency characteristic of tropical Andean ecosystems (Páramo de Chingaza), optical observations are restricted to cloud-free or low-cloud acquisition dates. 

The pipeline implements:
1. **Spectral Water Indexing:** Computes the Normalized Difference Water Index (NDWI; McFeeters, 1996) using the Green (B03) and Near-Infrared (B08) bands:
   $$\text{NDWI} = \frac{\text{B03 (Green)} - \text{B08 (NIR)}}{\text{B03 (Green)} + \text{B08 (NIR)}}$$
   *(Optionally computes MNDWI using SWIR Band 11).*
2. **Water Delineation & Thresholding:** Discriminates open surface water by applying adaptive or standard positive thresholding ($\text{NDWI} > 0.0$), with optional morphological opening/closing to suppress isolated speckle and cloud-shadow false positives.
3. **Vectorization & Official Coordinate Transformation:** Converts pixel clusters to vector geometries, clips with reservoir boundary masks, dissolves contiguous water bodies, and reprojects to the official metric coordinate reference system for Colombia: **MAGNA-SIRGAS 2018 / Origen Nacional (EPSG:9377)** or **UTM Zone 18N (EPSG:32618)** for planar area computation in $\text{km}^2$.
4. **Hydrological Cross-Validation:** Validates extracted optical areas against official in situ reference areas derived from daily water levels and bathymetric rating tables (reporting $r$, RMSE, MAE, and Bias).

---

## Automated Pipeline Execution (`run_sentinel_pipeline.py`)

Run the complete sequence for an individual Sentinel-2 scene with a single command:

```bash
python scripts/run_sentinel_pipeline.py \
  --green "/path/to/S2_B03_Green.tif" \
  --nir "/path/to/S2_B08_NIR.tif" \
  --boundary "/path/to/ChuzaReservoirShape.gpkg" \
  --obs "/path/to/chuza_obs.csv" \
  --output "/path/to/results" \
  --reservoir "chuza" \
  --date "2024-03-15"
```

---

## Direct Validation of Extracted Series (`validate_sentinel_area.py`)

If you have already processed multiple dates or want to analyze the consolidated time series table:

```bash
python scripts/validate_sentinel_area.py \
  --sentinel "data/sentinel2_time_series.csv" \
  --obs "/path/to/chuza_obs.csv" \
  --output "results/validation" \
  --reservoir "chuza"
```

---

## Component Scripts

| Script | Function |
| :--- | :--- |
| `run_sentinel_pipeline.py` | Master orchestrator coordinating extraction and validation. |
| `compute_ndwi.py` | Calculates continuous NDWI and MNDWI floating-point GeoTIFF rasters. |
| `extract_water_mask.py` | Thresholds continuous indices into binary water masks with morphological cleanup. |
| `polygonize_and_area.py` | Converts raster masks to vector polygons in EPSG:9377 and computes metric surface area. |
| `validate_sentinel_area.py` | Compares Sentinel-2 area series against in situ gauge data, plotting 1:1 scatter diagrams. |

---

## Dependencies & Installation

Install dependencies using:

```bash
pip install -r requirements.txt
```
