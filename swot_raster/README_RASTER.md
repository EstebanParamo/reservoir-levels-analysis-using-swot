# SWOT L2_HR_Raster Processing

This subfolder houses the end-to-end GIS and statistical diagnostic pipeline developed to extract, mosaic, filter, and validate water surface elevation (**wse**) and inundation area time series from the Surface Water and Ocean Topography (SWOT) High-Rate Raster product.

## Automated Processing Pipeline (`run_pipeline.py`)

You do not need to execute the individual scripts manually. The workflow features a master orchestrator `run_pipeline.py` that handles data dependencies and executes the entire pipeline sequentially via a single terminal command.

### Execution Command

Open your terminal, navigate into the `swot_raster/` directory, and run:

```bash
python scripts/run_pipeline.py --nc_dir /path/to/raw_netcdfs --shape /path/to/reservoir_polygon.shp --output /path/to/output_directory --pipeline_dir ./scripts
```
### 🔄 Internal Pipeline Architecture

When triggered, the pipeline coordinates the following processing phases across all 14 component scripts (kept fully unmodified):

#### Phase 1: Base Geospatial Ingestion
* `run_pipeline.py`: The master orchestrator that automatically triggers and coordinates the execution of all individual scripts using sequential sub-processes.
* `extract_layers.py`: Extracts primary bands (wse, water_area, sig0) along with their respective validation layers from raw NASA NetCDF granules.
* `mosaic.py`: Merges spatially overlapping orbit tiles recorded on the same date into single unified daily scenes.
* `clip.py`: Subsets and crops the daily combined scenes using the reservoir boundary shapefile.

#### Phase 2: Attribute Extraction & Statistical Cleansing
* `compute_statistics.py`: Calculates average elevations per track date and applies the evaluated filtering constraints (Limits, Percentiles, and K-STD criteria).
* `bitwise_decoder.py`: Unpacks and decodes 32-bit integer error flag masks into logical boolean arrays based on NASA's Table 15 specifications.

#### Phase 3: Tabular Quality Diagnostics
* `quality_analysis.py`: Evaluates standard quality layers to compute the percentage of reliable vs. degraded pixels per acquisition date.
* `error_summary_tables.py`: Scans bitwise flags over time to generate tabular CSV matrices detailing the active counts for each specific physical error.

#### Phase 4: Spatial Diagnostics & Mapping
* `error_frequency_maps.py`: Computes the pixel-by-pixel temporal frequency of quality flags and maps the dominant error source across the water body.
* `spatial_diagnostics.py`: Evaluates spatial degradation patterns, isolating shoreline geolocalization offsets from deep-water signal loss.

#### Phase 5: Temporal and Extent Consistency
* `temporal_diagnostics.py`: Evaluates chronological data consistency and isolates rapid elevation leaps using mathematical outlier detection.
* `coverage_analysis.py`: Cross-examines the theoretical reservoir polygon size against the real dynamic water surface area detected by SWOT.

#### Phase 6: Final Figures & Executive Reports
* `figures_generator.py`: Generates automated plots including WSE validation timelines, data distribution histograms, and quality-vs-error crossplots.
* `summary_report.py`: Compiles partial metrics from all stages into a final consolidated executive CSV report for immediate hydrological use.
