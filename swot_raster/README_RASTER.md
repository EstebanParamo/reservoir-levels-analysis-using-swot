# SWOT L2_HR_Raster Processing

This subfolder houses the end-to-end GIS and statistical diagnostic pipeline developed to extract, mosaic, filter, and validate water surface elevation (**wse**) and inundation area time series from the Surface Water and Ocean Topography (SWOT) High-Rate Raster product.

## Automated Processing Pipeline (`run_pipeline.py`)

You do not need to execute the individual scripts manually. The workflow features a master orchestrator `run_pipeline.py` that handles data dependencies and executes the entire pipeline sequentially via a single terminal command.

### Execution Command

Open your terminal, navigate into the `swot_raster/` directory, and run:

```bash
python scripts/run_pipeline.py --nc_dir /path/to/raw_netcdfs --shape /path/to/reservoir_polygon.shp --output /path/to/output_directory --pipeline_dir ./scripts
```
### Internal Pipeline Architecture

When triggered, the pipeline coordinates the following 3 processing phases across 14 component scripts (kept fully unmodified):

#### Phase 1: Base Geospatial Ingestion
* `extract_layers.py`: Extracts primary bands (`wse`, `water_area`, `sig0`) along with their respective bitwise quality flags from the raw NASA NetCDF granules.
* `mosaic.py`: Merges spatially overlapping orbit tiles (e.g., 073F, 074F) recorded on the same date into unified scenes.
* `clip.py`: Subsets the combined scenes using the reservoir boundary shapefile.

#### Phase 2: Attribute Extraction & Statistical Cleansing
* `compute_statistics.py`: Calculates average elevations per track date and applies the evaluated filtering constraints (*Limits*, *Percentiles*, and *K-STD* standard deviation criteria).
* `bitwise_decoder.py`: Decodes error integer flags into logical categories matching NASA’s Table 15 product specifications.

#### Phase 3: Quality Diagnostics & Report Compilation
* `quality_analysis.py` & `error_summary_tables.py`: Compute pixel degradation statistics and generate summary tables for active bitwise anomalies.
* `error_frequency_maps.py` & `spatial_diagnostics.py`: Map the spatial recurrence frequency of errors, locating persistent signal loss zones (e.g., shoreline layout vs. deep water).
* `temporal_diagnostics.py` & `coverage_analysis.py`: Check timeline series consistency and cross-examine theoretical reservoir boundary sizes against detected spatial extents.
* `figures_generator.py` & `summary_report.py`: Plot automated validation time series graphics and compile final diagnostic tables into structured CSV summaries.
