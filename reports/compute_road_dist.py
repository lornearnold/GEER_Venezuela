"""Populate `road_dist_m` on every candidate site = straight-line distance to the
nearest drivable road, in metres (EPSG:32619, rounded to 10 m).

Pure geometry, no live QGIS: reads the candidate GeoJSON and the drivable-roads
GeoJSON off disk and writes `road_dist_m` back into the candidate file, preserving
its structure. This is the drone "walk-in" gap for a driving team.

    uv run python reports/compute_road_dist.py            # write in place
    uv run python reports/compute_road_dist.py --dry-run  # print, don't write
    uv run python reports/compute_road_dist.py --only 111-123

CAUTION (CLAUDE.md): do NOT run this while QGIS has the candidate layer open — QGIS
caches the file and will flush its copy back over the write. Remove the layer first
(or close QGIS), run, then re-add a fresh layer.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.strtree import STRtree

REPO = Path(__file__).resolve().parent.parent
CANDIDATES = next(Path(p) for p in glob.glob(str(REPO / "data/landslide_candidates/*.geojson")))
ROADS = REPO / "data/routes/la-guaira_drivable.geojson"
UTM = "EPSG:32619"
ROUND_M = 10


def parse_only(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    out: set[int] = set()
    for part in spec.replace(" ", "").split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print, do not write")
    ap.add_argument("--only", help="restrict to site numbers, e.g. 111-123 or 3,4,94")
    args = ap.parse_args()
    only = parse_only(args.only)

    data = json.loads(CANDIDATES.read_text())

    roads = gpd.read_file(ROADS).to_crs(UTM)
    geoms = list(roads.geometry.values)
    tree = STRtree(geoms)

    to_utm = Transformer.from_crs("EPSG:4326", UTM, always_xy=True)

    changed = 0
    results: dict[int, int] = {}
    for feat in data["features"]:
        no = feat["properties"].get("site_no")
        if only is not None and no not in only:
            continue
        lon, lat = feat["geometry"]["coordinates"][:2]
        x, y = to_utm.transform(lon, lat)
        pt = shape({"type": "Point", "coordinates": (x, y)})
        nearest = geoms[tree.nearest(pt)]
        dist = int(round(pt.distance(nearest) / ROUND_M) * ROUND_M)
        results[no] = dist
        if feat["properties"].get("road_dist_m") != dist:
            changed += 1
        feat["properties"]["road_dist_m"] = dist

    for no in sorted(results):
        print(f"  site {no}: {results[no]} m")

    if args.dry_run:
        print(f"\n[dry-run] {len(results)} sites computed, {changed} would change; not written.")
        return

    CANDIDATES.write_text(json.dumps(data, ensure_ascii=False))
    print(f"\nwrote road_dist_m for {len(results)} sites ({changed} changed) -> "
          f"{CANDIDATES.relative_to(REPO)}")


if __name__ == "__main__":
    main()
