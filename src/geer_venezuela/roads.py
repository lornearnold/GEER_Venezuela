"""OpenStreetMap road network: arterial and drivable roads.

Roads come from OSM via the Overpass API (osmnx). OSM's `highway` tag encodes
functional class; arterials here = motorway, trunk, primary, secondary (+ links).
Data (c) OpenStreetMap contributors, ODbL.
"""

from __future__ import annotations

import geopandas as gpd
import osmnx as ox

ROADS_ATTRIBUTION = "Roads &copy; OpenStreetMap contributors (ODbL)"

#: Functional classes, most to least important, with display colors
ROAD_COLORS = {
    "motorway": "#e31a1c",
    "trunk": "#fd8d3c",
    "primary": "#fecc5c",
    "secondary": "#a6cee3",
}


def fetch_roads(
    bounds: tuple[float, float, float, float],
    classes: tuple[str, ...] = tuple(ROAD_COLORS),
) -> gpd.GeoDataFrame:
    """Arterial road lines within bounds (EPSG:4326) with `highway` class and `name`.

    `_link` ramps are folded into their parent class.
    """
    tags = {"highway": [c for base in classes for c in (base, f"{base}_link")]}
    features = ox.features_from_bbox(bounds, tags)
    lines = features[features.geometry.geom_type.isin(["LineString", "MultiLineString"])].copy()
    # OSM tags can be lists when a way carries multiple values
    lines["highway"] = lines["highway"].apply(lambda v: v[0] if isinstance(v, list) else v)
    lines["highway"] = lines["highway"].str.removesuffix("_link")
    lines = lines[lines["highway"].isin(classes)]
    if "name" not in lines.columns:
        lines["name"] = None
    keep = [c for c in ("name", "ref", "highway", "geometry") if c in lines.columns]
    return lines[keep].reset_index(drop=True)
