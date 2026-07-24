#!/usr/bin/env bash
# Run a PyQGIS script against the project WITHOUT the QGIS GUI.
#
#     ./scripts/run_headless.sh scripts/some_script.py
#
# Why this wrapper exists: PyQGIS is not a pip package. It ships compiled into
# QGIS.app and cannot be installed into the repo's uv venv - `uv add qgis` will
# not work, and `import qgis` from the venv only "succeeds" because this repo has
# a qgis/ *directory* that Python treats as a namespace package. It has no
# .core submodule; see scripts/README.md.
#
# So scripts that import qgis.* must run under QGIS's own interpreter, which
# needs three environment variables the app bundle normally sets for itself.
#
# CAVEAT: headless runs have no network/auth context, so streaming layers (NASA
# services, Esri basemaps) load INVALID with a Null extent. Anything that must
# see those layers has to run inside the GUI instead. The scripts in this
# directory only touch local dated rasters, so they are fine here.

set -euo pipefail

QGIS_APP="${QGIS_APP:-/Applications/QGIS.app}"

if [[ ! -d "$QGIS_APP" ]]; then
  echo "QGIS not found at $QGIS_APP — set QGIS_APP=/path/to/QGIS.app" >&2
  exit 1
fi

# Interpreter bundled with QGIS, plus the paths it expects.
export PYTHONHOME="$QGIS_APP/Contents/Frameworks"
export PROJ_DATA="$QGIS_APP/Contents/Resources/qgis/proj"   # else: "Cannot find proj.db"
export GDAL_DATA="$QGIS_APP/Contents/Resources/gdal"
PY="$QGIS_APP/Contents/MacOS/python3.12"

if [[ ! -x "$PY" ]]; then
  # Version-agnostic fallback if the bundled Python is bumped.
  PY="$(find "$QGIS_APP/Contents/MacOS" -maxdepth 1 -name 'python3*' -type f | head -1)"
  [[ -x "$PY" ]] || { echo "No bundled python found in $QGIS_APP/Contents/MacOS" >&2; exit 1; }
fi

exec "$PY" "$@"
