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
