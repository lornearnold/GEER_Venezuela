#!/bin/bash
# check_maxar_delivery_tiles.sh — validate the raw Maxar/Vantor tiles of a delivery on the
# One Touch drive: are all expected R#C# tiles present, openable, and decodable?
#
# Written for the la-guaira-west (S2AS_366001) delivery, whose Jul-15 VRT silently dropped
# tiles R2C04–R2C07 (→ 26.5 × 6.6 km black rectangle in the visual GeoTIFF). Run it with the
# drive mounted to learn whether those tiles exist-but-failed (rebuild the VRT) or are absent
# from the delivery (re-order from provider).
#
# Usage:
#   ./scripts/check_maxar_delivery_tiles.sh                 # default: la-guaira-west delivery
#   ./scripts/check_maxar_delivery_tiles.sh <delivery_dir> <filename_template> <rows> <cols>
#
# Template uses %d for row, %02d for column, e.g.:
#   '26JUN25142038-S2AS_R%dC%02d-200013366001_01_P001.TIF'
set -u

# --- QGIS-bundled GDAL 3.12 (system GDAL 3.3 lacks the JPEG codec) -------------------------
QGIS_APP="/Applications/QGIS.app"
export GDAL_DATA="$QGIS_APP/Contents/Resources/qgis/gdal"
export PROJ_LIB="$QGIS_APP/Contents/Resources/qgis/proj"
export PROJ_DATA="$PROJ_LIB"
export DYLD_LIBRARY_PATH="$QGIS_APP/Contents/MacOS/lib"
GDALINFO="$QGIS_APP/Contents/MacOS/gdalinfo"
GDALTRANSLATE="$QGIS_APP/Contents/MacOS/gdal_translate"
[ -x "$GDALINFO" ] || { echo "FATAL: $GDALINFO not found — is QGIS.app installed?"; exit 2; }

# --- Delivery under test -------------------------------------------------------------------
DELIVERY="${1:-/Volumes/One Touch/satellite_imagery/7013580666438136294/7013580666438136294}"
TEMPLATE="${2:-26JUN25142038-S2AS_R%dC%02d-200013366001_01_P001.TIF}"
ROWS="${3:-3}"
COLS="${4:-10}"
VRT="$(dirname "$0")/../data/basemaps/maxar_external/S2AS_366001_26JUN25.vrt"

[ -d "$DELIVERY" ] || { echo "FATAL: delivery dir not found (drive mounted?): $DELIVERY"; exit 2; }

echo "Delivery : $DELIVERY"
echo "Expecting: ${ROWS}x${COLS} grid = $((ROWS*COLS)) tiles"
echo

# --- Vendor's own tile manifest (.TIL), if present -----------------------------------------
TIL=$(ls "$DELIVERY"/*.TIL 2>/dev/null | head -1)
if [ -n "$TIL" ]; then
  n_til=$(grep -ci 'filename *=' "$TIL")
  echo ".TIL manifest: $(basename "$TIL") lists $n_til tiles"
  [ "$n_til" -ne $((ROWS*COLS)) ] && echo "  NOTE: differs from expected $((ROWS*COLS)) — trust the .TIL"
else
  echo ".TIL manifest: none found"
fi
echo

# --- Per-tile checks -----------------------------------------------------------------------
probe="${TMPDIR:-/tmp}/tile_probe_$$.tif"
n_ok=0; n_missing=0; n_bad=0; bad_tiles=(); missing_tiles=()
for r in $(seq 1 "$ROWS"); do
  for c in $(seq 1 "$COLS"); do
    f="$DELIVERY/$(printf "$TEMPLATE" "$r" "$c")"
    tag=$(printf "R%dC%02d" "$r" "$c")
    if [ ! -f "$f" ]; then
      echo "  $tag  MISSING"
      missing_tiles+=("$tag"); n_missing=$((n_missing+1)); continue
    fi
    sz=$(stat -f %z "$f")
    if [ "$sz" -eq 0 ]; then
      echo "  $tag  EMPTY (0 bytes)"
      bad_tiles+=("$tag"); n_bad=$((n_bad+1)); continue
    fi
    # openable? read size
    dims=$("$GDALINFO" "$f" 2>/dev/null | awk -F'[ ,]+' '/^Size is/{print $3, $4}')
    if [ -z "$dims" ]; then
      echo "  $tag  OPEN-FAIL ($(printf "%.1f" "$(echo "$sz/1048576" | bc -l)") MB)"
      bad_tiles+=("$tag"); n_bad=$((n_bad+1)); continue
    fi
    # decodable? pull a 512x512 window from the center (catches bled/corrupt JPEG blocks)
    w=$(echo "$dims" | cut -d' ' -f1); h=$(echo "$dims" | cut -d' ' -f2)
    if "$GDALTRANSLATE" -q -srcwin $((w/2-256)) $((h/2-256)) 512 512 "$f" "$probe" 2>/dev/null; then
      echo "  $tag  OK    (${w}x${h}, $(printf "%.0f" "$(echo "$sz/1048576" | bc -l)") MB)"
      n_ok=$((n_ok+1))
    else
      echo "  $tag  DECODE-FAIL (${w}x${h} — opens but center window won't read)"
      bad_tiles+=("$tag"); n_bad=$((n_bad+1))
    fi
    rm -f "$probe"
  done
done
rm -f "$probe"

# --- Compare with what the VRT actually used -----------------------------------------------
echo
if [ -f "$VRT" ]; then
  n_vrt=$(grep -c '<SourceFilename' "$VRT")
  echo "VRT check: $VRT"
  echo "  references $((n_vrt/8)) tiles per band ($n_vrt source entries / 8 bands)"
else
  echo "VRT not found at $VRT (skipping comparison)"
fi

# --- Verdict -------------------------------------------------------------------------------
echo
echo "SUMMARY: $n_ok OK, $n_missing missing, $n_bad bad of $((ROWS*COLS)) expected"
if [ "$n_missing" -gt 0 ]; then
  echo "  Missing: ${missing_tiles[*]}"
  echo "  -> tiles absent from delivery; re-request from provider (open data does NOT have this collect)"
fi
if [ "$n_bad" -gt 0 ]; then
  echo "  Bad:     ${bad_tiles[*]}"
  echo "  -> same failure family as puerto-cabello 'bled-JPEG'; try re-copying from source/zip"
fi
if [ "$n_missing" -eq 0 ] && [ "$n_bad" -eq 0 ]; then
  echo "  All tiles healthy -> the Jul-15 VRT build skipped good tiles; rebuild VRT + visual GeoTIFF"
  echo "     (recipe: maxar-external-drive-imagery memory / PROGRESS.md 2026-07-15 entry)"
fi
[ $((n_missing+n_bad)) -eq 0 ]
