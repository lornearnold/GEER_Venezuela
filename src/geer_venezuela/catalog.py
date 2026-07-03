"""Access helpers for the Planet Venezuela earthquake (2026-06-24) catalog on Source Cooperative.

Dataset: https://source.coop/planet/venezuela-earthquake-2026-06-24
Imagery (c) Planet Labs PBC, CC BY-NC 4.0.
"""

from __future__ import annotations

import duckdb
import geopandas as gpd
import pandas as pd
import shapely

BASE = "https://data.source.coop/planet/venezuela-earthquake-2026-06-24"

#: All 40 pre-event quarterly-basemap quads merged into one display COG (~4.8 m RGB).
PRE_EVENT_MOSAIC = f"{BASE}/pre-event/quarterly-mosaic/quarterly-mosaic-2026Q1_display.tif"

ATTRIBUTION = "Imagery &copy; Planet Labs PBC (CC BY-NC 4.0)"

#: Esri World Imagery Wayback, release 2026-05-28 (last full release before the earthquake).
#: Sub-meter in urban/coastal Venezuela; capture dates vary by tile — verify at
#: https://livingatlas.arcgis.com/wayback/ before citing a "before" date.
WAYBACK_PRE_EVENT = (
    "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/"
    "1.0.0/default028mm/MapServer/tile/10842/{z}/{y}/{x}"
)

WAYBACK_ATTRIBUTION = "Esri World Imagery Wayback (2026-05-28) &mdash; Esri, Maxar, Earthstar Geographics"

#: Esri World Hillshade — terrain-relief basemap tiles
HILLSHADE = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}"
)

HILLSHADE_ATTRIBUTION = "Terrain: Esri World Hillshade &mdash; Esri, Airbus DS, USGS, NGA, NASA, CGIAR"

#: Metadata service for the Wayback 2026-05-28 release (per-tile capture date/resolution)
_WAYBACK_METADATA = (
    "https://metadata.maptiles.arcgis.com/arcgis/rest/services/"
    "World_Imagery_Metadata_2026_r05/MapServer"
)


def wayback_capture_date(lat: float, lng: float) -> dict:
    """Capture date, resolution, and sensor of the Wayback BEFORE imagery at a point.

    Use this to cite the actual pre-event date for a specific site — the underlying
    photos are older than the 2026-05-28 release date (2024–early 2025 on most of the
    affected coast, but as old as 2021 in places).
    """
    import datetime
    import json
    import urllib.parse
    import urllib.request

    for layer in (4, 5, 6, 7, 8):  # 30 cm … 4.8 m metadata sublayers, finest first
        params = urllib.parse.urlencode(
            {
                "geometry": f"{lng},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "SRC_DATE2,SRC_RES,SRC_DESC",
                "returnGeometry": "false",
                "f": "json",
            }
        )
        with urllib.request.urlopen(f"{_WAYBACK_METADATA}/{layer}/query?{params}") as response:
            features = json.load(response).get("features") or []
        if features:
            attrs = features[0]["attributes"]
            ts = attrs.get("SRC_DATE2")
            return {
                "captured": (
                    datetime.datetime.fromtimestamp(ts / 1000, datetime.UTC).date().isoformat()
                    if ts
                    else None
                ),
                "resolution_m": attrs.get("SRC_RES"),
                "sensor": attrs.get("SRC_DESC"),
            }
    return {"captured": None, "resolution_m": None, "sensor": None}


def load_items(which: str = "post-event") -> gpd.GeoDataFrame:
    """Load the STAC-GeoParquet item index as a GeoDataFrame (EPSG:4326).

    which: "post-event" or "pre-event".
    """
    url = f"{BASE}/{which}/items.parquet"
    df = duckdb.sql(f"SELECT * FROM read_parquet('{url}')").fetchdf()
    geometry = shapely.from_wkb([bytes(g) for g in df.pop("geometry")])
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    if "datetime" in gdf.columns:
        gdf["datetime"] = pd.to_datetime(gdf["datetime"], utc=True)
        gdf = gdf.sort_values("datetime").reset_index(drop=True)
    return gdf


def locations(items: gpd.GeoDataFrame) -> pd.DataFrame:
    """Summarize post-event scenes by affected location."""
    return (
        items.groupby(["location", "location_slug"], as_index=False)
        .agg(
            scenes=("id", "count"),
            first=("datetime", "min"),
            last=("datetime", "max"),
            constellations=("constellation", lambda s: ", ".join(sorted(s.unique()))),
        )
        .sort_values("location")
        .reset_index(drop=True)
    )


def scenes_for(items: gpd.GeoDataFrame, location_slug: str) -> gpd.GeoDataFrame:
    """Post-event scenes for one location slug (e.g. "la-guaira"), oldest first."""
    out = items[items["location_slug"] == location_slug]
    if out.empty:
        available = sorted(items["location_slug"].unique())
        raise KeyError(f"No scenes for {location_slug!r}. Available: {available}")
    return out.reset_index(drop=True)


def asset_href(scene: pd.Series, asset: str = "visual") -> str:
    """Absolute COG URL for one asset ("visual", "analytic", "udm2", "udm") of a scene row."""
    assets = scene["assets"]
    if asset not in assets or assets[asset] is None:
        available = [k for k, v in assets.items() if v is not None]
        raise KeyError(f"Scene {scene['id']} has no {asset!r} asset. Available: {available}")
    return assets[asset]["href"]
