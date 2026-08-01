#!/usr/bin/env python
"""Fetch Parque Nacional Waraira Repano (El Ávila) limits from OSM.

Writes data/protected/waraira_repano.geojson (EPSG:4326, one polygon feature).
The park's southern limit follows the back of Caracas, so this is mainly a
reference boundary for the slopes above the city and the La Guaira coast.

Run from the repo root:

    uv run python scripts/fetch_protected_areas.py
    uv run python scripts/fetch_protected_areas.py --all   # every national park in bounds

Writes to disk; don't run while QGIS has the output layer open (QGIS caches the
file and flushes its copy back — remove the layer first, then re-add it).
"""

import argparse
from pathlib import Path

from geer_venezuela.protected import fetch_protected_areas, fetch_waraira_repano

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data/protected"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true",
                    help="keep every national park in bounds, not just Waraira Repano")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.all:
        gdf = fetch_protected_areas()
        default = OUT_DIR / "national_parks.geojson"
    else:
        gdf = fetch_waraira_repano()
        default = OUT_DIR / "waraira_repano.geojson"

    out = args.out or default
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GeoJSON")

    for _, row in gdf.iterrows():
        km2 = (
            gdf.loc[[row.name]].to_crs("EPSG:32619").area.iloc[0] / 1e6
        )
        print(f"{row['name']}  ({row.get('alt_name') or 'no alt_name'})  {km2:,.0f} km2")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
