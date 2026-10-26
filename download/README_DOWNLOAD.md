# Subproject: Automated SWOT Data Ingestion from NASA PO.DAAC

This directory provides automated scripts to query NASA's Common Metadata Repository (CMR) and download SWOT Level-2 high-rate datasets directly from the **Physical Oceanography Distributed Active Archive Center (PO.DAAC)**.

---

## Prerequisites: NASA Earthdata Login

SWOT products are publicly distributed free of charge, but access requires a free NASA Earthdata account.

1. Create an account at [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov/).
2. Approve the **PO.DAAC** application under your profile's authorized applications.
3. Configure your local authentication credentials in your home directory `~/.netrc`:

```bash
machine urs.earthdata.nasa.gov login <YOUR_USERNAME> password <YOUR_PASSWORD>
```

Set secure file permissions:
```bash
chmod 600 ~/.netrc
```

---

## 1. Python Download Pipeline (`download_swot_podaac.py`)

Leverages NASA's official `earthaccess` library for cloud-native search and multi-threaded retrieval.

```bash
pip install earthaccess
```

### Download LakeSP Vector Shapefiles (Orbit 104)
```bash
python download_swot_podaac.py \
  --product "lakesp" \
  --orbit 104 \
  --start_date "2023-09-01" \
  --end_date "2026-03-31" \
  --output "data/SWOT_LakeSP_104"
```

### Download High-Rate 100m Gridded Rasters
```bash
python download_swot_podaac.py \
  --product "raster" \
  --orbit 104 \
  --start_date "2023-09-01" \
  --end_date "2026-03-31" \
  --output "data/SWOT_Raster_100m_104"
```

---

## 2. Bash Download Script (`download_swot.sh`)

For headless server environments or automated cronjobs without complex Python dependencies:

```bash
bash download_swot.sh lakesp ./swot_lakesp_raw 2023-09-01T00:00:00Z 2026-03-31T23:59:59Z
```
