# Reservoir Levels Analysis Using Satellite Data (SWOT & Sentinel-2)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NASA SWOT](https://img.shields.io/badge/NASA%20PO.DAAC-SWOT%20L2-0052cc.svg)](https://podaac.jpl.nasa.gov/)
[![ESA Sentinel-2](https://img.shields.io/badge/ESA-Sentinel--2%20MSI-008080.svg)](https://sentinels.copernicus.eu/)

This repository centralizes the open-source GIS tools, automated processing pipelines, and statistical validation frameworks developed to evaluate the applicability and precision of **Surface Water and Ocean Topography (SWOT)** satellite altimetry and **Sentinel-2 MultiSpectral Instrument (MSI)** optical imagery for monitoring water storage dynamics in tropical continental reservoirs.

The methodology is developed and benchmarked on the **Chuza** and **San Rafael** reservoirs of the **Chingaza Water Supply System** (Colombia), which supplies ~70% of Bogotá's drinking water and underwent unprecedented water stress during the 2023–2024 El Niño drought.

---

## Repository Architecture

The codebase is organized into five specialized modules designed for independent execution and end-to-end reproducibility:

```
reservoir-levels-analysis-using-swot/
├── README.md                      # Main project documentation & benchmarking guide
├── requirements.txt               # Unified dependencies for the complete repository
│
├── swot_raster/                   # SWOT Level-2 High-Rate Gridded Raster (100m)
│   ├── scripts/                   # Automated 12-stage raster extraction & quality pipeline
│   ├── README_RASTER.md           # Technical guide & execution commands for raster data
│   └── requirements.txt
│
├── swot_lakesp/                   # SWOT Level-2 Lake Single-Pass (LakeSP) Vector
│   ├── scripts/                   # Shapefile ingestion, layover resolution & rating curves
│   ├── README_LAKESP.md           # Technical guide for LakeSP vector workflows
│   └── requirements.txt
│
├── sentinel/                      # Sentinel-2 Optical MSI Benchmark
│   ├── scripts/                   # NDWI/MNDWI calculation, water masking & EPSG:9377 vectorization
│   ├── data/                      # Reference validation time series
│   ├── README_SENTINEL.md         # Guide for optical remote sensing workflows
│   └── requirements.txt
│
├── validation/                    # Cross-Sensor Hydrological Validation Framework
│   ├── scripts/                   # r, RMSE, MAE, Bias metrics & publication figure generator
│   └── README_VALIDATION.md       # Complete intercomparison tables & performance metrics
│
└── download/                      # Automated NASA PO.DAAC Data Ingestion
    ├── download_swot_podaac.py    # Python search & download via earthaccess (Orbit 104)
    ├── download_swot.sh           # Headless Bash downloader via NASA Earthdata CMR
    └── README_DOWNLOAD.md         # Credentials configuration guide
```

---

## Key Hydrological Benchmarks

Validation against in situ daily hydrometric gauge records provided by the Bogotá Water and Sewerage Company (EAAB) across the 2023–2026 monitoring window:

### 1. Water Surface Elevation (WSE)
* **Chuza (LakeSP Vector):** Exceptional performance ($r = 0.996$, $\text{RMSE} = 1.440\text{ m}$, $\text{MAE} = 1.190\text{ m}$, $\text{Bias} = +1.012\text{ m}$), reproducing continuous operational drawdown and refill cycles.
* **Chuza (Raster 100m Limits Filter):** High agreement ($r = 0.921$, $\text{RMSE} = 4.770\text{ m}$).
* **San Rafael:** Substantial improvement following transition to processing-chain version D, with WSE correlations exceeding $r = 0.95$ and $\text{RMSE} = 3.70\text{ m}$.

### 2. Surface Water Area & Volume
* **Sentinel-2 Optical NDWI:** Substantially outperformed radar-derived area estimates ($r = 0.729$ in Chuza, $r = 0.808$ in San Rafael), though constrained by high cloud cover typical of Andean páramo ecosystems.
* **Storage Volume (LakeSP):** In Chuza, the mean absolute error represented only **1.7%** of the reservoir's usable capacity ($223\text{ hm}^3$), demonstrating operational readiness for municipal water management.

---

## Quickstart

### 1. Installation

Clone this repository and create a clean environment:

```bash
git clone https://github.com/EstebanParamo/reservoir-levels-analysis-using-swot.git
cd reservoir-levels-analysis-using-swot

# Install unified requirements
pip install -r requirements.txt
```

### 2. Run SWOT Raster Pipeline

Execute the master orchestrator for gridded SWOT NetCDF granules:

```bash
python swot_raster/scripts/run_pipeline.py \
  --nc "/path/to/swot_raster_netcdf" \
  --shape "/path/to/reservoir_boundary.gpkg" \
  --output "results/raster" \
  --pipeline "swot_raster/scripts"
```

*(See [swot_raster/README_RASTER.md](swot_raster/README_RASTER.md) for detailed flags).*

### 3. Run SWOT LakeSP Vector Pipeline

Execute the end-to-end vector pipeline (handling layover correction and bathymetric volume conversion):

```bash
python swot_lakesp/scripts/run_lakesp_pipeline.py \
  --lakesp_dir "/path/to/swot_lakesp_zips" \
  --obs_csv "/path/to/gauge_obs.csv" \
  --output "results/lakesp" \
  --reservoir "chuza"
```

*(See [swot_lakesp/README_LAKESP.md](swot_lakesp/README_LAKESP.md) for detailed flags).*

### 4. Run Sentinel-2 Water Mask Pipeline

```bash
python sentinel/scripts/run_sentinel_pipeline.py \
  --green "/path/to/B03.tif" \
  --nir "/path/to/B08.tif" \
  --boundary "/path/to/boundary.gpkg" \
  --obs "/path/to/gauge_obs.csv" \
  --output "results/sentinel" \
  --reservoir "chuza" \
  --date "2024-03-15"
```

*(See [sentinel/README_SENTINEL.md](sentinel/README_SENTINEL.md) for detailed flags).*

### 5. Multi-Sensor Intercomparison & Report Compilation

Compile the unified accuracy benchmark tables:

```bash
python validation/scripts/compare_products.py --output "results/validation"
```

---

## Academic Citation

If you use this codebase, processing pipelines, or validation findings in your research, please cite:

```bibtex
@mastersthesis{Leal2026SWOT,
  author       = {Jorge Luis Leal Noy},
  title        = {Validaci{\'o}n de los niveles de agua en los embalses de San Rafael y Chuza del Sistema Chingaza usando el sat{\'e}lite Surface Water and Ocean Topography (SWOT)},
  school       = {Universidad Nacional de Colombia, Facultad de Ingenier{\'i}a},
  year         = {2026},
  address      = {Bogot{\'a}, Colombia},
  type         = {Tesis de Maestr{\'i}a en Ingenier{\'i}a -- Recursos Hidr{\'a}ulicos}
}

@article{LealParamo2026SWOT,
  author       = {Jorge Luis Leal Noy and Esteban P{\'a}ramo and Andr{\'e}s and Erasmo Alfredo Rodr{\'i}guez Sandoval and Luis Alejandro Morales Mar{\'i}n},
  title        = {Assessment of SWOT satellite altimetry products for reservoir water level and storage monitoring in tropical high-mountain ecosystems},
  journal      = {Journal of Hydrology / Remote Sensing of Environment (In Review)},
  year         = {2026}
}
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
