# reservoir-levels-analysis-with-swot

**Analysis of reservoir water surface elevation (WSE) by comparing SWOT satellite data with in situ measurements.**  
This project processes SWOT Raster and LakeSP products to extract Water Surface Elevation (wse) to compare them whit real in situ measurements.

---

## Raster processing

Main script (SWOT_wse_RASTER_PROCESSING.py) create mosaics per date, clip to a reservoir polygon, compute statistics with user-defined elevation bounds (`min`, `max`), and produce plots.


### Features
- Extracts WSE data from SWOT raster (.nc) files.
- Clips rasters using reservoir shapefiles (.shp or .gpkg).
- Mosaics rasters per acquisition date.
- Calculates average WSE per date within a defined elevation range.
- Generates visual plots and CSV outputs.

---
  
### Quick start

#### 1. Clone repository
```bash
git clone https://github.com/<YOUR-USERNAME>/reservoir-levels-analysis-with-swot.git
cd reservoir-levels-analysis-with-swot
```
---


#### 2. Run the script
```bash
For Windows (example):

python "C:\path\to\SWOT_wse_RASTER_PROCESSING.py" `
--input "C:\path\to\NC_folder" `
--shape "C:\path\to\clip_shape.gpkg" `
--output "C:C:\path\to\output_folder" `
--min 1000 --max 3500
```
```bash
For macOS/Linux (example):

python3 "/path/to/RASTER_PROCESSING_VF_ENG_argparse.py" \
  --input "/path/to/NC_folder" \
  --shape "/path/to/clip_shape.gpkg" \
  --output "/path/to/output_folder" \
  --min 2900 \
  --max 3010
```
---
#### 3. Output
```bash
- CSV file containing average WSE and statistics per date.
- Plots SWOT-derived average WSE.
- Clipped and mosaicked raster files for reference.
```
---
#### Notes
```bash
Ensure all dependencies are installed.
```
