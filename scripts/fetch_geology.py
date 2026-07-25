#!/usr/bin/env python3
"""Fetch surface geology polygons for the study region -> data/terrain/geology.geojson.

Source: Macrostrat vector tiles (CC-BY), which in this region serve the digitized
USGS Geologic Map of Venezuela 1:750k (Hackley et al. 2005). See
src/geer_venezuela/geology.py for the tile-decode/dissolve details.

Bounds cover the full earthquake study region, Puerto Cabello to La Guaira
(per Lorne, 2026-07-24: UR 10.7/-66.4, LL 10.0/-69.3).

Usage: uv run python scripts/fetch_geology.py
(If TLS certificate errors appear: SSL_CERT_FILE=$(uv run python -c
"import certifi; print(certifi.where())") uv run python scripts/fetch_geology.py)
"""

from pathlib import Path

from geer_venezuela import fetch_geology

BOUNDS = (-69.3, 10.0, -66.4, 10.7)  # minx, miny, maxx, maxy (EPSG:4326)
OUT = Path(__file__).resolve().parent.parent / "data/terrain/geology.geojson"

units = fetch_geology(BOUNDS)
units.to_file(OUT, driver="GeoJSON")
print(f"wrote {OUT}: {len(units)} units, extent {tuple(round(v, 3) for v in units.total_bounds)}")
