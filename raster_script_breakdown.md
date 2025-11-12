# Script breakdown: SWOT_wse_RASTER_PROCESSING_Vx.py
## Overview

This script processes SWOT satellite raster data (NetCDF format) to extract Water Surface Elevation (WSE) time series from a defined reservoir polygon.

It performs the following major steps:
1. Reads and mosaics multiple .nc rasters per acquisition date.
2. Clips them to a reservoir boundary (.shp or .gpkg).
3. Filters valid pixels based on selected statistical methods.
4. Calculates mean, min, max, and standard deviation for each date.
5. Produces CSV tables and publication-quality plots.

---

## Library summary and rationale

| Library               | Purpose                                                                                        |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| **os, re**            | File handling, directory creation, and filename parsing.                                       |
| **rasterio**          | Read/write raster data (GeoTIFFs and NetCDFs), handle spatial metadata, clipping, and merging. |
| **geopandas**         | Read shapefiles/GeoPackages defining reservoir boundaries.                                     |
| **numpy, pandas**     | Numerical and tabular operations (arrays, statistics, CSV export).                             |
| **matplotlib**        | Generate time-series plots of WSE.                                                             |
| **xarray, rioxarray** | Open NetCDF data efficiently and preserve geospatial metadata.                                 |
| **datetime**          | Handle timestamps and date extraction for file naming and output labeling.                     |
| **argparse**          | Command-line interface for easy execution with different folders, bounds, and methods.         |

---

## Code structure

The entire code is organized into a class-based structure:
```bash
class SWOTRasterProcessor:
    ...
```
This allows:
- Modular processing (easy to extend and debug)
- State management (directories, limits, selected methods)
- Cleaner main execution logic.

---

# Function-by-function Explanation

### **1. `__init__()` — Initialization**

**Purpose:**
Sets up all input/output paths, reads the shapefile, and prepares output directories.

**Key operations:**

* Loads the reservoir polygon using **GeoPandas**.
* Creates subfolders for mosaics, clipped rasters, CSVs, and plots.
* Defines placeholders for user-defined limits and processing mode.

---

### **2. `find_nc_files()`**

**Purpose:**
Scans the input directory for all NetCDF (`.nc`) files to be processed.

**Key operations:**

* Uses `os.walk()` to find all `.nc` files recursively.
* Sorts them alphabetically to ensure chronological consistency.

---

### **3. `group_by_date()`**

**Purpose:**
Groups `.nc` files by acquisition date extracted from filenames (using regex).

**Key operations:**

* Parses filenames to detect the date (e.g., `20230904`).
* Creates a dictionary: `{ date: [list_of_files_for_that_date] }`.

---

### **4. `mosaic_nc_files()`**

**Purpose:**
Merges all rasters from a single date into one mosaic raster.

**Key operations:**

* Opens all `.nc` files for that date with **rioxarray.open_rasterio()**.
* Uses `rasterio.merge.merge()` to combine them into a single dataset.
* Saves the mosaic to the `mosaics` subfolder.

---

### **5. `clip_to_shape()`**

**Purpose:**
Clips each mosaic raster to the reservoir polygon.

**Key operations:**

* Reads the shapefile boundary (in GeoDataFrame format).
* Uses **rasterio.mask.mask()** to extract only pixels inside the reservoir.
* Writes clipped rasters to the `clipped` subfolder.

---

### **6. `calculate_mean()`**

**Purpose:**
Computes mean WSE and basic statistics (min, max, std) for each clipped raster.

**Modes supported:**

1. **Manual:** Uses fixed user-provided `min` and `max` limits.
2. **Percentile:** Automatically sets limits from chosen percentiles (e.g., 5–95%).
3. **Standard Deviation:** Uses mean ± (N × std), with `N` user-defined.
4. **All:** Runs all three methods and generates combined CSV/plots.

**Key operations:**

* Reads pixel values from clipped rasters.
* Masks invalid or nodata values.
* Applies the filtering criteria.
* Computes summary statistics with NumPy.
* Saves results into CSV files per method.

---

### **7. `plot_results()`**

**Purpose:**
Creates publication-ready plots showing the WSE evolution through time.

**Key operations:**

* Reads statistics CSV files.
* Generates three types of plots for each method:

  * Line plot (only mean)
  * Line + range band
  * Line + standard deviation band
* Adds dynamic titles and legends including:

  * Reservoir name
  * Method type
  * Statistical parameters (e.g., percentile range or std factor)
* Saves plots under the corresponding dated and method-labeled subfolder.

---

### **8. `combine_all_modes()`**

**Purpose:**
When `--mode all` is selected, it runs **all three filtering modes** sequentially and produces:

* Individual outputs for each method.
* A combined CSV summarizing all WSE statistics in one table.
* Comparative plots overlaying the results of all methods.

**Why:**
This enables side-by-side comparison of the three filtering approaches, showing how sensitive the statistics are to the chosen outlier rejection criteria.

---

### **9. `run_all()`**

**Purpose:**
The main orchestrator — runs all pipeline stages in sequence:

1. Locate input rasters
2. Group by date
3. Mosaic each date
4. Clip by shapefile
5. Compute statistics
6. Generate plots

---

### **10. `main` block (`if __name__ == "__main__":`)**

**Purpose:**
Enables execution from the terminal with arguments.
Parses the following inputs:

| Argument         | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| `--input`        | Folder containing `.nc` SWOT files.                        |
| `--shape`        | Path to reservoir shapefile (`.shp` or `.gpkg`).           |
| `--output`       | Output directory for results.                              |
| `--mode`         | Processing mode (`manual`, `percentile`, `std`, or `all`). |
| `--min`, `--max` | Manual elevation limits.                                   |
| `--percentiles`  | Lower and upper percentiles for automatic filtering.       |
| `--std_factor`   | Standard deviation multiplier (default = 2).               |

---

## Example of workflow

1. Input:

   * `/SwotRasterData/*.nc`
   * `/ReservoirShape.gpkg`

2. Run:

   ```bash
   python SWOT_wse_RASTER_PROCESSING_Vx.py --input ... --shape ... --output ... --mode all
   ```

3. Output:

   * `/mosaics/`, `/clipped/`, `/csv/`, `/plots/`
   * Individual and combined plots
   * Summary CSV with statistics per method

---

## Summary

| Step | Function              | Description                                 |
| ---- | --------------------- | ------------------------------------------- |
| 1    | `find_nc_files()`     | Discover input rasters                      |
| 2    | `group_by_date()`     | Group files per acquisition date            |
| 3    | `mosaic_nc_files()`   | Create single raster per date               |
| 4    | `clip_to_shape()`     | Extract reservoir area                      |
| 5    | `calculate_mean()`    | Apply statistical filtering and compute WSE |
| 6    | `plot_results()`      | Plot WSE through time                       |
| 7    | `combine_all_modes()` | Run all methods and compare results         |
| 8    | `run_all()`           | Main execution workflow                     |

---
