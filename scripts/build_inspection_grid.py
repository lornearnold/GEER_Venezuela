#!/usr/bin/env python3
"""Build the two-tier MGRS inspection grid -> data/grids/inspection_grid.gpkg.

Two polygon layers on the standard MGRS/UTM 19N kilometer grid (REGVEN, the
Venezuelan national system, is WGS84/UTM-compatible at sub-meter level):

    grid_10km   ~300 cells,  cell_id like '19PGM45'   (MGRS 10 km precision)
    grid_1km    100 children per parent, '19PGM4256'  (MGRS 1 km precision),
                parent_id links each to its 10 km cell

Both carry show (0/1, default 0 = curtained). The 'show' field is working
inspection state, toggled from the QGIS canvas via a layer action — it doubles
as the record of which cells have been systematically inspected.

Extent: the study region (LL 10.0/-69.3, UR 10.7/-66.4 — same as the geology
layer), snapped outward to 10 km UTM boundaries. Entirely within zone 19N /
band P, but the MGRS lettering below is computed, not hardcoded.

Usage: uv run python scripts/build_inspection_grid.py
Re-running overwrites the GeoPackage — remove the layers from QGIS first
(CLAUDE.md file-cache gotcha), and note it resets any inspection state.
"""

from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import box

BOUNDS_4326 = (-69.3, 10.0, -66.4, 10.7)  # study region, W S E N
UTM = "EPSG:32619"
OUT = Path(__file__).resolve().parent.parent / "data/grids/inspection_grid.gpkg"

# MGRS 100 km square lettering (AA scheme, WGS84).
_COL_SETS = {1: "ABCDEFGH", 2: "JKLMNPQR", 0: "STUVWXYZ"}
_ROWS = "ABCDEFGHJKLMNPQRSTUV"
_BANDS = "CDEFGHJKLMNPQRSTUVWX"  # 8-degree latitude bands from 80S


def mgrs_prefix(zone: int, easting: float, northing: float, lat: float) -> str:
    band = _BANDS[min(int((lat + 80) // 8), len(_BANDS) - 1)]
    col = _COL_SETS[zone % 3][int(easting // 100_000) - 1]
    row_idx = int(northing // 100_000) % 20
    if zone % 2 == 0:
        row_idx = (row_idx + 5) % 20
    return f"{zone}{band}{col}{_ROWS[row_idx]}"


def cell_id(zone: int, e: float, n: float, lat: float, size: int) -> str:
    prefix = mgrs_prefix(zone, e, n, lat)
    e_in, n_in = int(e % 100_000), int(n % 100_000)
    if size == 10_000:
        return f"{prefix}{e_in // 10_000}{n_in // 10_000}"
    return f"{prefix}{e_in // 1_000:02d}{n_in // 1_000:02d}"


def main() -> None:
    to_utm = Transformer.from_crs("EPSG:4326", UTM, always_xy=True)
    to_ll = Transformer.from_crs(UTM, "EPSG:4326", always_xy=True)
    w, s, e, n = BOUNDS_4326
    xs, ys = zip(*(to_utm.transform(x, y) for x in (w, e) for y in (s, n)))
    e0, e1 = int(min(xs) // 10_000) * 10_000, -(-int(max(xs)) // 10_000) * 10_000
    n0, n1 = int(min(ys) // 10_000) * 10_000, -(-int(max(ys)) // 10_000) * 10_000

    cells10, cells1 = [], []
    for ce in range(e0, e1, 10_000):
        for cn in range(n0, n1, 10_000):
            lat = to_ll.transform(ce + 5_000, cn + 5_000)[1]
            pid = cell_id(19, ce, cn, lat, 10_000)
            cells10.append({"cell_id": pid, "show": 0,
                            "geometry": box(ce, cn, ce + 10_000, cn + 10_000)})
            for se in range(ce, ce + 10_000, 1_000):
                for sn in range(cn, cn + 10_000, 1_000):
                    cells1.append({"cell_id": cell_id(19, se, sn, lat, 1_000),
                                   "parent_id": pid, "show": 0,
                                   "geometry": box(se, sn, se + 1_000, sn + 1_000)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf10 = gpd.GeoDataFrame(cells10, crs=UTM)
    gdf1 = gpd.GeoDataFrame(cells1, crs=UTM)
    gdf10.to_file(OUT, layer="grid_10km", driver="GPKG")
    gdf1.to_file(OUT, layer="grid_1km", driver="GPKG", mode="a")
    print(f"wrote {OUT}")
    print(f"  grid_10km: {len(gdf10)} cells ({gdf10.cell_id.iloc[0]} .. {gdf10.cell_id.iloc[-1]})")
    print(f"  grid_1km : {len(gdf1)} cells")
    print(f"  UTM extent E {e0}..{e1}, N {n0}..{n1}")
    print(f"  100km squares: {sorted(set(c['cell_id'][:5] for c in cells10))}")


if __name__ == "__main__":
    main()
