# Subproject: SWOT L2_HR_LakeSP Vector Processing & Validation

This subfolder contains the modular pipeline developed to ingest, filter, disambiguate, and validate hydrological parameters (water surface elevation **wse**, surface area **area_detct**, and storage volume) derived from the **SWOT Level-2 High-Rate Lake Single-Pass (LakeSP)** vector data product.

The pipeline is tailored to handle complex inland reservoir morphologies (specifically tested and validated on the **Chuza** and **San Rafael** reservoirs of the Chingaza Water Supply System in the tropical high Andes of Colombia).

---

## Key Methodological Features

* **Direct Multi-Format Ingestion:** Reads either uncompressed `.shp` shapefiles or compressed `.zip` granules downloaded directly from NASA PO.DAAC.
* **Water-Water Layover Resolution:** Detects and resolves geometric distortion where Prior Lake Database (PLD) boundaries cause spurious expansions of `area_total` (reaching 17–19 km² in San Rafael). The pipeline automatically standardizes on `area_detct` (pure radar backscatter detection), increasing the observed correlation from 0.363 to 0.560.
* **Bathymetric Rating Curves:** Converts SWOT water surface elevations into storage volumes (hm³) using official reservoir elevation-volume rating curves calibrated with EAAB / ENEL bathymetric surveys.
* **Intrinsic Quality Diagnostics:** Decodes NASA's 32-bit integer error mask (`qual_f_b`) into discrete physical causes (e.g., radar classification suspect, geolocation uncertainty, wse variability) and evaluates categorical quality flags (`quality_f`).
* **Uncertainty Cross-Validation:** Compares internally declared SWOT uncertainty metrics (`wse_u`, `wse_std`, `area_tot_u`) against true validation errors relative to in situ daily hydrometric gauge observations (evaluating standardized anomalies and percentage within $\pm \sigma$ error bands).

---

## Automated Pipeline Execution (`run_lakesp_pipeline.py`)

The subproject features a master orchestrator `run_lakesp_pipeline.py` that executes all processing steps sequentially via a single terminal command.

### Execution Command

Navigate into the `swot_lakesp/` directory and run:

#### For Chuza Reservoir
```bash
python scripts/run_lakesp_pipeline.py \
  --lakesp_dir "/path/to/SWOT_L2_HR_LakeSP_Prior_104" \
  --obs_csv "/path/to/chuza_obs.csv" \
  --output "/path/to/results/chuza" \
  --reservoir "chuza"
```

#### For San Rafael Reservoir
```bash
python scripts/run_lakesp_pipeline.py \
  --lakesp_dir "/path/to/SWOT_L2_HR_LakeSP_Prior_104" \
  --obs_csv "/path/to/san_rafael_obs.csv" \
  --output "/path/to/results/san_rafael" \
  --reservoir "san_rafael"
```

---

## Component Scripts Architecture

| Script | Purpose |
| :--- | :--- |
| `run_lakesp_pipeline.py` | Master orchestrator coordinating all processing phases. |
| `extract_lake_attributes.py` | Ingests shapefiles/ZIPs, extracts key hydrological and quality attributes, and filters target reservoirs. |
| `resolve_layover.py` | Disambiguates multiple passes on the same day and resolves water-water layover phenomena. |
| `volume_estimation.py` | Interpolates water levels into storage volume using official bathymetric rating tables. |
| `quality_analysis.py` | Computes categorical quality distribution (Good, Suspect, Degraded, Bad). |
| `bitwise_decoder.py` | Decodes the 32-bit integer `qual_f_b` into boolean physical flags and generates frequency tables. |
| `uncertainty_analysis.py` | Compares declared uncertainty vs. actual validation error, computing standardized anomalies. |
| `figures_generator.py` | Produces publication-grade 1:1 scatter plots, time series, and error band figures. |

---

## Installation & Dependencies

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

### Main Packages
* `geopandas` & `shapely`: Vector shapefile ingestion and geographic manipulation.
* `pandas` & `numpy`: Tabular consolidation, time series alignment, and metric calculations.
* `matplotlib`: Scientific plotting of validation series, scatter diagrams, and error bands.
* `scipy`: Bathymetric curve interpolation.
