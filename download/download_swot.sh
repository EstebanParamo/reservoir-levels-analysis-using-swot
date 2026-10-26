#!/usr/bin/env bash
# ==============================================================================
# download_swot.sh
# ------------------------------------------------------------------------------
# Automated Bash script to query and download SWOT Level-2 products (Raster & LakeSP)
# from NASA PO.DAAC using NASA Earthdata Login credentials stored in ~/.netrc.
#
# Requirements:
#   - curl, jq
#   - NASA Earthdata account with active ~/.netrc authentication:
#       machine urs.earthdata.nasa.gov login <USER> password <PASSWORD>
#
# Usage:
#   bash download_swot.sh <raster|lakesp> <output_dir> [start_date] [end_date]
# ==============================================================================

set -euo pipefail

PRODUCT="${1:-lakesp}"
OUTPUT_DIR="${2:-./swot_downloads}"
START_DATE="${3:-2023-09-01T00:00:00Z}"
END_DATE="${4:-2026-03-31T23:59:59Z}"

# Chingaza Reservoir Bounding Box: [west, south, east, north]
BBOX="-73.85,4.55,-73.65,4.85"

if [ "$PRODUCT" == "raster" ]; then
    SHORTNAME="SWOT_L2_HR_Raster_100m_2.0"
elif [ "$PRODUCT" == "lakesp" ]; then
    SHORTNAME="SWOT_L2_HR_LakeSP_2.0"
else
    echo "Unknown product: $PRODUCT. Allowed: raster, lakesp"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
COOKIE_JAR=$(mktemp)

echo "================================================================="
echo " Querying NASA CMR for: $SHORTNAME (Orbit 104)"
echo " Period: $START_DATE to $END_DATE"
echo " Destination: $OUTPUT_DIR"
echo "================================================================="

CMR_URL="https://cmr.earthdata.nasa.gov/search/granules.json?short_name=${SHORTNAME}&bounding_box=${BBOX}&temporal=${START_DATE},${END_DATE}&page_size=2000"

GRANULE_URLS=$(curl -s "$CMR_URL" | jq -r '.feed.entry[].links[] | select(.rel | endswith("/data#")) | .href' | grep "_104_" || true)

COUNT=$(echo "$GRANULE_URLS" | grep -c "http" || true)
echo "Found $COUNT granules matching Orbit 104."

if [ "$COUNT" -eq 0 ]; then
    echo "No matching granules found. Verify dates and orbit."
    rm -f "$COOKIE_JAR"
    exit 0
fi

echo "$GRANULE_URLS" | while read -r URL; do
    [ -z "$URL" ] && continue
    FILENAME=$(basename "$URL")
    DEST="$OUTPUT_DIR/$FILENAME"
    if [ -f "$DEST" ]; then
        echo "Already exists: $FILENAME (skipping)"
        continue
    fi
    echo "Downloading: $FILENAME"
    curl -b "$COOKIE_JAR" -c "$COOKIE_JAR" -L --netrc -o "$DEST" "$URL"
done

rm -f "$COOKIE_JAR"
echo "Download complete."
