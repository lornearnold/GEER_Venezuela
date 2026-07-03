"""Surface geology from Macrostrat (CC-BY 4.0).

In this region Macrostrat serves the digitized USGS *Geologic Map of Venezuela*,
1:750,000 (Hackley, Urbani, Karlsen & Garrity, 2005; USGS OFR 2005-1038 / DS-199).
Vector tiles are decoded locally into polygons with unit name, lithology, age and
suggested color.
"""

from __future__ import annotations

import math
import tempfile
import urllib.request
from pathlib import Path

import geopandas as gpd
import pandas as pd

#: XYZ raster tiles for direct display in leafmap/QGIS
MACROSTRAT_TILE_URL = "https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png"

MACROSTRAT_MVT_URL = "https://tiles.macrostrat.org/carto/{z}/{x}/{y}.mvt"

GEOLOGY_ATTRIBUTION = (
    "Geology: Macrostrat (CC-BY) / USGS Geologic Map of Venezuela 1:750k (Hackley et al. 2005)"
)

_KEEP_COLUMNS = ["name", "age", "lith", "descrip", "t_int", "b_int", "color", "ref_name"]


def _tile_index(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    n = 2**zoom
    x = int((lon + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y


def fetch_geology(bounds: tuple[float, float, float, float], zoom: int = 11) -> gpd.GeoDataFrame:
    """Geologic unit polygons covering bounds (EPSG:4326), merged across tile seams."""
    minx, miny, maxx, maxy = bounds
    x0, y1 = _tile_index(minx, miny, zoom)  # y grows southward
    x1, y0 = _tile_index(maxx, maxy, zoom)
    parts = []
    with tempfile.TemporaryDirectory() as tmp:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                tile = Path(tmp) / f"{zoom}_{x}_{y}.mvt"
                urllib.request.urlretrieve(
                    MACROSTRAT_MVT_URL.format(z=zoom, x=x, y=y), tile
                )
                if tile.stat().st_size == 0:
                    continue
                gdf = gpd.read_file(f"MVT:{tile}", layer="units", X=x, Y=y, Z=zoom)
                # not every tile carries every attribute column
                for column in _KEEP_COLUMNS:
                    if column not in gdf.columns:
                        gdf[column] = None
                parts.append(gdf[["map_id", *_KEEP_COLUMNS, "geometry"]])
    units = pd.concat(parts, ignore_index=True)
    units = units[units["name"] != "water"]
    # dissolve duplicates of the same polygon split across tile boundaries
    units = units.dissolve(by="map_id", aggfunc="first").reset_index()
    units = units.to_crs("EPSG:4326")
    return units.clip(list(bounds)).reset_index(drop=True)


def geology_at(lat: float, lng: float) -> pd.DataFrame:
    """Point query: which geologic unit(s) underlie this location (Macrostrat API)."""
    import json

    url = f"https://macrostrat.org/api/v2/geologic_units/map?lat={lat}&lng={lng}"
    with urllib.request.urlopen(url) as response:
        data = json.load(response)["success"]["data"]
    return pd.DataFrame(data)[["name", "strat_name", "lith", "t_int_name", "b_int_name"]]
