"""Protected-area boundaries from OpenStreetMap.

The one that matters here is Parque Nacional Waraira Repano — the massif north
of Caracas, still widely called El Ávila (renamed in 2011; OSM carries the new
name, `alt_name` keeps the old one). Its southern limit runs along the back of
the city, so the boundary doubles as a useful reference line for where the
slopes above Caracas and the Vargas/La Guaira coast begin.

Boundaries come from OSM relations via the Overpass API (osmnx). A national-park
relation's member ways each come back as their own row, so the parts are
dissolved into one feature per park.
Data (c) OpenStreetMap contributors, ODbL.
"""

from __future__ import annotations

import geopandas as gpd
import osmnx as ox

PROTECTED_ATTRIBUTION = "Protected areas &copy; OpenStreetMap contributors (ODbL)"

#: OSM relation id for Parque Nacional Waraira Repano (El Ávila).
WARAIRA_REPANO_REL = 3375647

#: Bounds (W, S, E, N) comfortably containing the Caracas / La Guaira massif.
AVILA_BOUNDS = (-67.2, 10.4, -66.2, 10.7)


def fetch_protected_areas(
    bounds: tuple[float, float, float, float] = AVILA_BOUNDS,
    boundary: str = "national_park",
) -> gpd.GeoDataFrame:
    """National-park polygons within bounds (EPSG:4326), one row per park.

    Returns `name`, `alt_name`, `protect_class` and `geometry`. Multi-part
    relations are dissolved so each park is a single (Multi)Polygon.
    """
    features = ox.features_from_bbox(bounds, {"boundary": boundary})
    polys = features[features.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if polys.empty:
        return polys

    for col in ("name", "alt_name", "protect_class"):
        if col not in polys.columns:
            polys[col] = None
    # OSM tags can be lists when a way carries multiple values.
    for col in ("name", "alt_name", "protect_class"):
        polys[col] = polys[col].apply(lambda v: v[0] if isinstance(v, list) else v)

    # Member ways of one relation repeat the parent's tags — dissolve to one
    # feature per park so the layer has a single boundary to draw and label.
    dissolved = polys.dissolve(by="name", as_index=False, dropna=False)
    keep = ["name", "alt_name", "protect_class", "geometry"]
    return dissolved[keep].reset_index(drop=True)


def fetch_waraira_repano() -> gpd.GeoDataFrame:
    """Just Parque Nacional Waraira Repano (El Ávila), as a single feature."""
    parks = fetch_protected_areas()
    park = parks[parks["name"].astype(str).str.contains("Waraira", case=False, na=False)]
    if park.empty:
        raise SystemExit("Waraira Repano not found in the OSM response")
    return park.reset_index(drop=True)
