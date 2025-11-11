# reservoir-levels-analysis-with-swot

**Analysis of reservoir water surface elevation (WSE) by comparing SWOT satellite data with in situ measurements.**  

This project processes SWOT Raster and LakeSP products to extract Water Surface Elevation (wse) to compare them with real in situ measurements.

---

## Raster processing

Main script (SWOT_wse_RASTER_PROCESSING.py) create mosaics per date, clip to a reservoir polygon, compute statistics with user-defined elevation bounds (`min`, `max`), and produce plots.


### Features
- Extracts WSE data from SWOT raster (NetCDF format) files.
- Clips rasters to specific reservoir boundaries using provided shapefiles (.shp or .gpkg).
- Combines multiple rasters into a single mosaic for each acquisition date (if necessary).
- Computes the average WSE per date using one of three methods:
  1. **Manual Filter**: Uses user-defined minimum and maximum elevation limits to filter valid pixels.
  2. **Percentile Filter**: Automatically sets lower and upper limits based on user-defined statistical percentiles (e.g., 5th and 95th) to exclude outliers.
  3. **Standard Deviation Filter**: Uses the mean ± (N × standard deviation) to exclude extreme values, where **N** is a user-defined factor.
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
--output "C:\path\to\output_folder" `
--mode manual `
--min 2900 `
--max 3010
```
```bash
For macOS/Linux (example):

python3 "/path/to/RASTER_PROCESSING_VF_ENG_argparse.py" \
  --input "/path/to/NC_folder" \
  --shape "/path/to/clip_shape.gpkg" \
  --output "/path/to/output_folder" \
  --mode manual --min 2900 --max 3010
```
```bash
# For the Percentile filter:
--mode auto_percentil --percentiles 5 95

# For the Standard Deviation filter:
--mode auto_std --std_factor 2
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
