# Reservoir Levels Analysis using SWOT and Sentinel-2 

This repository centralizes the GIS tools, processing pipelines, and statistical validation methodologies developed to monitor water surface elevation (WSE) and surface area dynamics in continental reservoirs (specifically **Chuza** and **San Rafael**). The project incorporates multi-product satellite data to evaluate hydrological performance against gauge observations (OBS series).

## Project Repository Structure

To ensure scalable collaboration and maintain methodological independence across sensors and data structures, the project is organized into dedicated subsections:

1. **`swot_raster/` (SWOT L2_HR_Raster):** Automated pipeline and data-quality diagnostics based on the high-resolution gridded raster products from the SWOT mission. *(Developed by Esteban Páramo)*.
2. **`swot_lake_sp/` (SWOT LakeSP):** Processing modules tailored for the vector database polygon products mapping lakes and continental water bodies.
3. **`sentinel2/` (Sentinel-2 MSI):** Water-mask extraction algorithms and spectral indices workflows (e.g., MNDWI) using optical imagery from the ESA constellation.

---

## Getting Started

Each subfolder contains its own technical documentation, execution instructions, and independent environment configuration dependencies. 

* To explore or run the workflows for the SWOT high-resolution raster datasets, please navigate directly to the **[swot_raster/](./swot_raster)** subfolder and read its specific user guide.
