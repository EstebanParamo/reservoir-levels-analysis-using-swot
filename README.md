# reservoir-levels-analysis-using-swot

**Automated analysis of reservoir Water Surface Elevation (WSE) by comparing SWOT satellite data with in situ measurements.**  

This project processes SWOT Raster and LakeSP products to extract Water Surface Elevation (wse) to compare them with real in situ measurements.

---

## Raster processing module

Main script: (SWOT_wse_RASTER_PROCESSING_Vx.py) 
This script performs all preprocessing, clipping, and analysis tasks automatically.
It creates date-stamped mosaics, clips data to reservoir boundaries, applies statistical filters, computes per-date statistics, and generates organized visual and tabular outputs.

### Features
- Extracts WSE data from SWOT raster (NetCDF format) files.
- Clips rasters to specific reservoir boundaries using provided shapefiles (.shp or .gpkg).
- Combines multiple rasters into a single mosaic for each acquisition date (if necessary).
- Calculates per-date statistics using one of three selectable filtering methods:
  1. **Manual Filter**: Uses user-defined minimum and maximum elevation limits to filter valid pixels.
  2. **Percentile Filter**: Automatically sets lower and upper limits based on user-defined statistical percentiles (e.g., 5th and 95th) to exclude outliers.
  3. **Standard Deviation Filter**: Uses the mean ± (N × standard deviation) to exclude extreme values, where **N** is a user-defined factor.
- Optional **--mode all** runs all three methods in one execution, generating:
  - Individual results subfolders for each method.
  - Individual plots and CSVs per method.
  - A combined comparison plot of all three methods.
  - A summary CSV consolidating all methods averages and statistics.
- Generates visual plots and CSV outputs:
  - 9 plots in total: 3 per method (simple line, range band, and std band) and 3 combined comparison plots (one per visualization tipe).
- Each output is date-stamped and labeled with the reservoir name and method in both filenames and plot titles.
- Fully compatible whit macOS, Windows and Linux.
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
For Windows (example) for (mode all):

python "C:\path\to\SWOT_wse_RASTER_PROCESSING_V4.py" --input "C:\path\to\NC_folder" --shape "C:\path\to\clip_shape.gpkg" --output "C:\path\to\output_folder" --mode all --percentiles 10 90 --std_factor 2 --min 2900 --max 3010
```
```bash
For macOS/Linux (example) for (mode all):

python3 "/path/to/SWOT_wse_RASTER_PROCESSING_V4.py" --input "/path/to/NC_folder" --shape "/path/to/clip_shape.gpkg" --output "/path/to/output_folder" --mode all --percentiles 10 90 --std_factor 2 --min 2900 --max 3010
```
```bash
# For the Percentile filter:
--mode auto_percentil --percentiles 5 95

# For the Standard Deviation filter:
--mode auto_std --std_factor 2
```
---
```bash
# Mode Options
| Mode         | Description                                                                             | Adjustable Parameters                             |
| ------------ | --------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `manual`     | Uses fixed elevation limits.                                                            | `--min`, `--max`                                  |
| `percentile` | Filters outliers based on data percentiles.                                             | `--percentiles <low> <high>`                      |
| `std`        | Filters values within mean ± N × std.                                                   | `--std_factor <N>`                                |
| `all`        | Runs all three methods, creates subfolders, combined comparison plots, and summary CSV. | `--min`, `--max`, `--percentiles`, `--std_factor` |

```
---
#### 3. Output
##### General output data
```bash
- CSV file containing average WSE and statistics per date.
- Plots SWOT-derived average WSE.
- Clipped and mosaicked raster files for reference.
```
##### Output folders structure
```bash
📁 all_methods_2025-11-11/
│
├── 📁 manual/
│   ├── wse_results_manual.csv
│   ├── plot_manual_lines.png
│   ├── plot_manual_range_band.png
│   └── plot_manual_std_band.png
│
├── 📁 percentile/
│   ├── wse_results_percentile.csv
│   ├── plot_percentile_lines.png
│   ├── plot_percentile_range_band.png
│   └── plot_percentile_std_band.png
│
├── 📁 std/
│   ├── wse_results_std.csv
│   ├── plot_std_lines.png
│   ├── plot_std_range_band.png
│   └── plot_std_std_band.png
│
├── 📄 combined_summary.csv
└── 📊 combined_comparison_plots.png

Each CSV includes per-date mean WSE and key statistics for the given method, while the summary CSV consolidates all results for comparison.
```
---
#### Notes
```bash
- Outputs are automatically date-stamped using local time.
- The reservoir name (from the shapefile) is used in filenames and plot titles.
- All plots include the method name, reservoir name, and statistical parameters in their titles and legends.
- The code is fully compatible with macOS, Windows, and Linux.
- Ideal for integration in reproducible workflows or publication figures.
```
