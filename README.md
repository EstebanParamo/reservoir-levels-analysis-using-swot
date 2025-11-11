# reservoir-levels-analysis-with-swot

**Analysis of reservoir water surface elevation (WSE) by comparing SWOT satellite data with in situ measurements.**  
This project processes SWOT raster products to extract Water Surface Elevation, create mosaics per date, clip to a reservoir polygon, compute statistics with user-defined elevation bounds (min, max), and produce plots.

## Quick start

1. Clone repository:
```bash
git clone <YOUR-REPO-URL>
cd reservoir-levels-analysis-with-swot

2. Run the cript (example):
```bash
For macOS:
python3 SWOT_wse_RASTER_PROCESSING.py" \
  --input "/path/to/NC_folder" \
  --shape "/path/to/clip_shape.gpkg" \
  --output "/path/to/output_folder" \
  --min 2900 \
  --max 3010

For Windows:
python "C:\SWOT_wse_RASTER_PROCESSING.py" `
--input "C:\path\to\NC_folder" `
--shape "C:\path\to\clip_shape.gpkg" `
--output "C:C:\path\to\output_folder" `
--min 1000 --max 3500
