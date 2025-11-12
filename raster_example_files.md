# example_files

**Download example files here: https://drive.google.com/drive/folders/1kxwThl7Sq1aPVZq_4A3tkr5nk6iRi_X5?usp=share_link**  

---
## Reservoir Information

- Chuza Reservoir shapefile (ChuzaReservoirShape.gpkg)
- Located in: Colombia
- Primary source of water for Bogotá

## Why Two Scenes Are Needed

The Chuza Reservoir spans the southern portion of SWOT scene 073F and the northern portion of scene 074F. Located directly on the boundary between these two scenes, the reservoir requires both to capture complete water surface elevation (WSE) data. Using only one scene would result in significant data gaps, as each scene alone covers only part of the reservoir's full extent.

## SWOT RASTER DATA

This example dataset allows you to test the script with real SWOT data and a reservoir shapefile. The files include:

- Clip shape (.gpkg) for Chuza reservoir.

- **.nc** files from SWOT raster scenes **073F and 074F**, dates included:
  - 2023/09/04
  - 2023/10/16
  - 2023/11/06
  - 2023/11/27
  - 2023/12/17

## Example raster files structure
```bash
📁 swot_raster_example_files/
│
├── ChuzaReservoirShape.gpkg
│
├── 📁 nc_example_files/
│   ├── SWOT_L2_HR_Raster_100m_UTM18N_N_x_x_x_003_104_073F_20230904T154702_20230904T154723_PGC0_01.nc
│   ├── SWOT_L2_HR_Raster_100m_UTM18N_N_x_x_x_003_104_073F_20230904T154702_20230904T154723_PGC0_01.nc
│   ├── SWOT_L2_HR_Raster_100m_UTM18N_N_x_x_x_005_104_073F_20231016T091709_20231016T091730_PGC0_01.nc
│   ├── SWOT_L2_HR_Raster_100m_UTM18N_N_x_x_x_005_104_074F_20231016T091729_20231016T091750_PGC0_01.nc
│   └── ...
│
└── 📁 output/
```
## How to run the script
### Basic Syntax for running all filtering methods 
* (go to README.md for more information)
```bash
For Windows (example) for (mode all):

python "C:\path\to\SWOT_wse_RASTER_PROCESSING_V4.py" --input "C:\path\to\NC_folder" --shape "C:\path\to\clip_shape.gpkg" --output "C:\path\to\output_folder" --mode all --percentiles 10 90 --std_factor 2 --min 2900 --max 3010
```
```bash
For macOS/Linux (example) for (mode all):

python3 "/path/to/SWOT_wse_RASTER_PROCESSING_V4.py" --input "//path/to/NC_folder" --shape "/path/to/clip_shape.gpkg" --output "/path/to/output_folder" --mode all --percentiles 10 90 --std_factor 2 --min 2900 --max 3010
```

