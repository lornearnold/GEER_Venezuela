#!/bin/zsh
# open_qgis.sh — launch QGIS with the GEER project, protected against the vsicurl hang.
#
# The Vantor stream layers are /vsicurl COGs on S3 with DigitalGlobe-style names; on load,
# GDAL probes S3 for .IMD/.RPB/etc sidecars for every one of them. On a slow connection each
# probe waits out full network timeouts and project load hangs for minutes (see PROGRESS.md
# 2026-07-29). These env vars make non-.tif requests fail instantly and cap HTTP stalls.
# Launching the binary directly (not `open -a`) is what lets the vars reach QGIS.
#
# Usage:  scripts/open_qgis.sh          # opens qgis/geer_venezuela.qgz
#         scripts/open_qgis.sh <path>   # opens another project/file

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:-$REPO/qgis/geer_venezuela.qgz}"

export CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff"   # the fix: only .tif may go over HTTP
export GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"        # no remote directory listings
export GDAL_HTTP_CONNECTTIMEOUT="10"
export GDAL_HTTP_TIMEOUT="20"
export GDAL_HTTP_MAX_RETRY="1"

exec /Applications/QGIS.app/Contents/MacOS/QGIS "$PROJECT"
