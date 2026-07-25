#!/usr/bin/env bash
# Download Vantor Open Data scenes (Venezuela-Earthquake-Jun-2026) not already
# held in this project. Resumable: re-running skips complete files and resumes
# partial ones, so it is safe to interrupt and restart.
#
# Usage:
#   ./scripts/download_vantor_opendata.sh                  # 43 scenes, ~327 GB
#   INCLUDE_MOSAIC_SCENES=1 ./scripts/download_vantor_opendata.sh  # +3 Jun-25 LG01 scenes (~8 GB)
#   ./scripts/download_vantor_opendata.sh /some/other/dest
#
# Excluded by default:
#   B16000110179D310 / B16000110179D410 — same collects as the two Maxar-delivered
#     la-guaira 2026-06-25 21:29 scenes already in data/basemaps/maxar_visual/.
#   B110001100BB2210/2310/2510 (Jun-25 LG01) — source scenes of the local
#     vantor_legion_20260625_mosaic.tif; set INCLUDE_MOSAIC_SCENES=1 for full-res.
#
# Each scene gets <ID>.tif (visual COG) plus <ID>.json (STAC item metadata),
# sorted into pre_event/ and post_event/ subfolders.
set -uo pipefail

DEST="${1:-/Volumes/One Touch/satellite_imagery/vantor_open_data}"
BASE="https://vantor-opendata.s3.amazonaws.com/events/Venezuela-Earthquake-Jun-2026"

# phase vehicle acquired(UTC) catalog_id bytes
SCENES=(
  "pre LG03 20251103_125633 B130001101BE2A00 2955456830"
  "pre LG03 20251104_123929 B130001101BF9600 7758895755"
  "pre LG01 20260131_151724 B110001100029010 4163233247"
  "pre LG04 20260209_120336 B1400011000BDF10 4729195795"
  "pre LG05 20260319_212351 B150001101008110 3557685530"
  "pre LG06 20260320_144655 B160001100FD1910 4722307642"
  "pre LG05 20260320_210810 B150001101015C10 4250849467"
  "pre LG06 20260321_143132 B160001100FF4510 12785294065"
  "pre LG02 20260407_151446 B120001100513B10 3698062933"
  "pre WV03 20260531_145727 10400100B979DD00 55008896131"
  "post WV03 20260626_150937 B040001100075610 17670640139"
  "post WV03 20260626_150950 B040001100075510 19271866928"
  "post WV03 20260626_151035 B040001100074D10 14055248090"
  "post LG06 20260626_211346 B1600011017A8610 6521783380"
  "post LG05 20260627_134810 B15000110186C610 3852241461"
  "post LG05 20260627_134836 B15000110186C710 4535817941"
  "post LG05 20260627_134855 B15000110186C810 5242204008"
  "post WV02 20260627_151415 B0300011000DF210 4519750507"
  "post WV02 20260627_151423 B0300011000DF410 4440486876"
  "post WV02 20260627_151431 B0300011000DF510 4828105394"
  "post WV02 20260627_151442 B0300011000E1810 6260969287"
  "post WV02 20260627_151458 B0300011000DF610 4492509854"
  "post WV02 20260627_151506 B0300011000DFB10 4453624640"
  "post WV02 20260627_151521 B0300011000DFC10 5645531606"
  "post WV02 20260627_151531 B0300011000DFE10 5527833376"
  "post GE01 20260627_151550 B050001100041D10 6676556555"
  "post LG02 20260627_153017 B120001100BECE10 6261970948"
  "post LG02 20260627_153037 B120001100BED010 7339923681"
  "post WV02 20260628_143613 B030001100114010 2694629238"
  "post LG05 20260629_131448 B150001101890A10 14876113022"
  "post LG05 20260629_131508 B150001101890C10 12067824530"
  "post LG05 20260629_131531 B150001101891610 12131508769"
  "post LG05 20260629_131617 B150001101890E10 11021976207"
  "post LG05 20260629_131645 B150001101890B10 3319216230"
  "post LG04 20260629_140932 B140001100B5C710 11213214326"
  "post LG04 20260629_140955 B140001100B5C810 11674519046"
  "post LG04 20260629_141016 B140001100B5CA10 11567724287"
  "post GE01 20260629_144927 B05000110006BA10 8151965623"
  "post GE01 20260629_144955 B05000110006BD10 6341114965"
  "post LG06 20260629_202315 B1600011017D8B10 3249327702"
  "post LG06 20260629_202422 B1600011017D8D10 2613510524"
  "post LG06 20260629_202521 B1600011017D9010 2850219231"
  "post LG05 20260630_125955 B1500011018A1110 2291941948"
)
if [[ "${INCLUDE_MOSAIC_SCENES:-0}" == "1" ]]; then
  SCENES+=(
    "post LG01 20260625_151646 B110001100BB2210 2447661423"
    "post LG01 20260625_151707 B110001100BB2310 2845732958"
    "post LG01 20260625_151749 B110001100BB2510 3567269552"
  )
fi

if [[ ! -d "$(dirname "$DEST")" ]]; then
  echo "Destination parent $(dirname "$DEST") not found — is the external drive mounted?" >&2
  exit 1
fi
mkdir -p "$DEST/pre_event" "$DEST/post_event"

total=${#SCENES[@]} n=0 fetched=0 skipped=0 failed=0
for entry in "${SCENES[@]}"; do
  read -r phase vehicle dt id bytes <<< "$entry"
  n=$((n + 1))
  dir="$DEST/${phase}_event"
  tif="$dir/$id.tif"
  if [[ -f "$tif" && "$(stat -f%z "$tif")" == "$bytes" ]]; then
    echo "[$n/$total] $id ($vehicle $dt) — already complete, skipping"
    skipped=$((skipped + 1))
    continue
  fi
  gb=$(awk -v b="$bytes" 'BEGIN {printf "%.1f", b / 1073741824}')
  echo "[$n/$total] $id ($vehicle $dt, ${gb} GB) -> $dir/"
  if ! curl -fSL --retry 5 --retry-delay 10 -C - -o "$tif" "$BASE/$id.tif"; then
    echo "  FAILED: $id" >&2
    failed=$((failed + 1))
    continue
  fi
  if [[ "$(stat -f%z "$tif")" != "$bytes" ]]; then
    echo "  SIZE MISMATCH: $id (expected $bytes, got $(stat -f%z "$tif"))" >&2
    failed=$((failed + 1))
    continue
  fi
  curl -fsSL --retry 5 -o "$dir/$id.json" "$BASE/$id.json" \
    || echo "  warning: metadata fetch failed for $id" >&2
  fetched=$((fetched + 1))
done

echo
echo "Done: $fetched downloaded, $skipped already present, $failed failed (of $total)."
if [[ $failed -gt 0 ]]; then
  echo "Re-run the script to resume/retry failures."
  exit 1
fi
