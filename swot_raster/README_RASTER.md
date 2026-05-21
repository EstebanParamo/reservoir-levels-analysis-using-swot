# Subproject: SWOT L2_HR_Raster Processing

This subfolder houses the end-to-end GIS and statistical diagnostic pipeline developed to extract, mosaic, filter, and validate water surface elevation (**wse**) and inundation area time series from the Surface Water and Ocean Topography (SWOT) High-Rate Raster product.

> **Note on Reproducibility:** > While this repository was developed and validated using the **Chuza** and **San Rafael** reservoirs as primary case studies, the pipeline is fully modular and agnostic. These scripts are designed to be highly reproducible; you can adapt them to any reservoir or lake of interest by simply updating the input data paths and the corresponding boundary vector file (shapefile/GeoPackage). This framework serves as a robust base or inspiration for further hydrological research and operational monitoring.

---

## Automated Processing Pipeline (`run_pipeline.py`)

You do not need to execute the individual scripts manually. The workflow features a master orchestrator `run_pipeline.py` that handles data dependencies and executes the entire pipeline sequentially via a single terminal command.

### Execution Command

Open your terminal, navigate into the `swot_raster/` directory, and run the pipeline command matching your system environment.

#### For Windows (PowerShell / Command Prompt)
```bash
python scripts/run_pipeline.py `
  --nc "C:\path\to\your\data\nc_files" `
  --shape "C:\path\to\your\data\shape\YourReservoir.gpkg" `
  --output "C:\path\to\your\results" `
  --pipeline "C:\path\to\your\pipeline"
```
#### For Linux / macOS (Bash / Zsh)
```bash
python scripts/run_pipeline.py \
  --nc "/path/to/your/data/nc_files" \
  --shape "/path/to/your/data/shape/YourReservoir.gpkg" \
  --output "/path/to/your/results" \
  --pipeline "/path/to/your/pipeline"
```
---

## Internal Pipeline Architecture

When triggered, the pipeline coordinates the following processing phases across all component scripts. 

### Phase 1: Base Geospatial Ingestion
* **run_pipeline.py**: Master orchestrator for automated sequential execution.
* **extract_layers.py**: Extracts primary bands (wse, water_area, sig0) and validation layers from raw NASA NetCDF granules.
* **mosaic.py**: Merges spatially overlapping orbit tiles into single unified daily scenes.
* **clip.py**: Subsets and crops the daily combined scenes using the provided reservoir boundary.

### Phase 2: Attribute Extraction & Statistical Cleansing
* **compute_statistics.py**: Calculates average elevations and applies filtering constraints (Limits, Percentiles, and K-STD criteria).
* **bitwise_decoder.py**: Decodes 32-bit integer error flag masks into logical boolean arrays based on NASA's product specifications.

### Phase 3: Tabular Quality Diagnostics
* **quality_analysis.py**: Evaluates quality layers to compute pixel reliability metrics.
* **error_summary_tables.py**: Scans bitwise flags to generate CSV matrices detailing active physical error counts.

### Phase 4: Spatial Diagnostics & Mapping
* **error_frequency_maps.py**: Computes the pixel-by-pixel temporal frequency of quality flags and maps dominant error sources.
* **spatial_diagnostics.py**: Evaluates spatial degradation patterns, isolating shoreline offsets from signal loss.

### Phase 5: Temporal and Extent Consistency
* **temporal_diagnostics.py**: Evaluates chronological consistency and detects rapid elevation outliers.
* **coverage_analysis.py**: Cross-examines theoretical reservoir polygon size against SWOT-detected dynamic water surface area.

### Phase 6: Final Figures & Executive Reports
* **figures_generator.py**: Generates automated plots (WSE validation timelines, histograms, and quality-vs-error crossplots).
* **summary_report.py**: Compiles all metrics into a consolidated executive CSV report for immediate hydrological use.
