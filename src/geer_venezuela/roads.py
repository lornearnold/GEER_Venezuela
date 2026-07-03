"""OpenStreetMap road network: arterials and steep-slope watch segments.

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

_UTM = "EPSG:32619"


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


def watch_segments(
    roads: gpd.GeoDataFrame,
    steep: gpd.GeoDataFrame,
    distance_m: float = 100,
) -> gpd.GeoDataFrame:
    """Road segments within distance_m of steep-slope polygons — where field teams
    should watch for landslide evidence while driving. Returns EPSG:4326 lines
    with `length_km` per segment."""
    roads_utm = roads.to_crs(_UTM)
    zone = steep.to_crs(_UTM).union_all().buffer(distance_m)
    segments = gpd.clip(roads_utm, zone).explode(index_parts=False)
    segments = segments[segments.geometry.geom_type == "LineString"].copy()
    segments["length_km"] = (segments.length / 1000).round(3)
    segments = segments[segments["length_km"] >= 0.05]  # drop slivers under 50 m
    return segments.to_crs("EPSG:4326").reset_index(drop=True)
