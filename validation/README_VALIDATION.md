# Multi-Sensor Hydrological Validation & Accuracy Benchmark

This module centralizes the quantitative validation framework, error metric calculations, and multi-sensor intercomparisons across:
* **In Situ Observations:** Official daily hydrometric gauge records (water level, surface area, and stored volume) provided by the Bogotá Water and Sewerage Company (EAAB).
* **SWOT L2_HR_LakeSP:** Lake Single-Pass vector polygon product.
* **SWOT L2_HR_Raster_100m:** High-Rate gridded raster product under multiple statistical filtering schemes (RAW, Limits, Percentile, and K-STD).
* **Sentinel-2 MSI Level-2A:** High-resolution optical water surface area estimates derived from the Normalized Difference Water Index (NDWI).

---

## Validation Summary Benchmarks (Chingaza System 2023–2026)

### 1. Water Surface Elevation (WSE)

| Sensor / Product | Reservoir | Method / Filter | $N$ | $r$ (Pearson) | RMSE (m) | MAE (m) | Bias (m) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **SWOT LakeSP** | Chuza | Nominal | 38 | **0.996** | **1.440** | **1.190** | +1.012 |
| **SWOT LakeSP** | San Rafael | Nominal | 38 | 0.773 | 9.262 | 7.594 | −7.175 |
| **SWOT Raster** | Chuza | RAW | 36 | 0.483 | 27.200 | 10.160 | −8.140 |
| **SWOT Raster** | Chuza | Limits | 36 | **0.921** | **4.770** | **1.860** | +1.470 |
| **SWOT Raster** | Chuza | Percentile | 36 | 0.747 | 9.370 | 3.230 | +0.560 |
| **SWOT Raster** | Chuza | K-STD | 36 | 0.906 | 5.170 | 2.330 | +1.220 |
| **SWOT Raster** | San Rafael | RAW | 36 | 0.282 | 14.220 | 9.330 | +8.910 |
| **SWOT Raster** | San Rafael | Limits | 36 | 0.348 | 12.490 | 8.200 | +7.320 |
| **SWOT Raster** | San Rafael | Percentile | 36 | 0.368 | 11.980 | 7.900 | +5.640 |
| **SWOT Raster** | San Rafael | K-STD | 36 | 0.387 | 10.790 | 7.550 | +4.300 |
| **SWOT Raster** | San Rafael (Post-Jul 2025) | K-STD | 13 | **0.952** | **3.700** | **3.530** | +3.360 |

### 2. Surface Water Area

| Sensor / Product | Reservoir | Method | $N$ | $r$ (Pearson) | RMSE ($\text{km}^2$) | MAE ($\text{km}^2$) | Bias ($\text{km}^2$) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **SWOT LakeSP** | Chuza | `area_detct` | 38 | −0.090 | 2.038 | 1.725 | −1.678 |
| **SWOT LakeSP** | San Rafael | `area_detct` | 38 | 0.560 | 0.785 | 0.656 | +0.577 |
| **SWOT Raster** | Chuza | Pixel Sum | 36 | −0.009 | 1.848 | 1.644 | −1.644 |
| **SWOT Raster** | San Rafael | Pixel Sum | 36 | −0.199 | 0.878 | 0.496 | −0.496 |
| **Sentinel-2** | Chuza | NDWI > 0.0 | 9 | **0.729** | **0.637** | **0.515** | −0.515 |
| **Sentinel-2** | San Rafael | NDWI > 0.0 | 29 | **0.808** | **0.428** | **0.344** | −0.314 |

### 3. Reservoir Storage Volume

| Reservoir | Usable Capacity | $N$ | $r$ (Pearson) | RMSE ($\text{hm}^3$) | MAE ($\text{hm}^3$) | Bias ($\text{hm}^3$) | MAE (% Usable) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Chuza** | $223\text{ hm}^3$ | 38 | **0.998** | **5.085** | **3.780** | +3.019 | **1.7%** |
| **San Rafael** | $70\text{ hm}^3$ | 38 | 0.751 | 21.096 | 17.356 | −15.698 | 24.8% |

---

## Running the Comparative Scripts

To compile the consolidated CSV tables:

```bash
python scripts/compare_products.py --output "results/consolidated"
```

To generate publication figures:

```bash
python scripts/generate_paper_figures.py --output "results/figures"
```
