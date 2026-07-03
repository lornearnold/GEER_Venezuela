"""Copernicus GLO-30 DEM access and slope derivation.

DEM: Copernicus GLO-30 (30 m global), public COGs on AWS Open Data
(https://registry.opendata.aws/copernicus-dem/). (c) DLR/ESA, free to use.
Reads are windowed from the remote COGs — only the AOI is downloaded.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from rasterio.merge import merge
from rasterio.warp import Resampling, calculate_default_transform, reproject

COP30_URL = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM/"
    "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM.tif"
)

#: UTM zone 19N — covers the whole affected region (72°W–66°W)
UTM_CRS = "EPSG:32619"


def dem_tile_urls(bounds: tuple[float, float, float, float]) -> list[str]:
    """URLs of the 1-degree GLO-30 tiles intersecting (minx, miny, maxx, maxy) in EPSG:4326."""
    minx, miny, maxx, maxy = bounds
    urls = []
    for lat in range(math.floor(miny), math.floor(maxy) + 1):
        for lon in range(math.floor(minx), math.floor(maxx) + 1):
            lat_s = f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}"
            lon_s = f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}"
            urls.append(COP30_URL.format(lat=lat_s, lon=lon_s))
    return urls


def fetch_dem(bounds: tuple[float, float, float, float], out_file: str | Path) -> Path:
    """Mosaic and clip the GLO-30 DEM to bounds (EPSG:4326); write a GeoTIFF, return its path.

    Skips tiles missing from the bucket (pure-ocean tiles are not published).
    """
    out_file = Path(out_file)
    if out_file.exists():
        return out_file
    sources = []
    for url in dem_tile_urls(bounds):
        try:
            sources.append(rasterio.open(url))
        except RasterioIOError:
            continue
    if not sources:
        raise ValueError(f"No GLO-30 tiles found for bounds {bounds}")
    array, transform = merge(sources, bounds=bounds)
    meta = sources[0].meta | {
        "height": array.shape[1],
        "width": array.shape[2],
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
    }
    for src in sources:
        src.close()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_file, "w", **meta) as dst:
        dst.write(array)
    return out_file


def compute_slope(dem_file: str | Path, out_file: str | Path) -> Path:
    """Slope in degrees from a lat/lon DEM: reproject to UTM 19N at 30 m, then Horn gradient."""
    out_file = Path(out_file)
    if out_file.exists():
        return out_file
    with rasterio.open(dem_file) as src:
        transform, width, height = calculate_default_transform(
            src.crs, UTM_CRS, src.width, src.height, *src.bounds, resolution=30
        )
        elevation = np.empty((height, width), dtype="float32")
        reproject(
            source=rasterio.band(src, 1),
            destination=elevation,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=UTM_CRS,
            resampling=Resampling.bilinear,
        )
    dzdy, dzdx = np.gradient(elevation, 30.0)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype("float32")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_file,
        "w",
        driver="GTiff",
        height=slope.shape[0],
        width=slope.shape[1],
        count=1,
        dtype="float32",
        crs=UTM_CRS,
        transform=transform,
        compress="deflate",
        tiled=True,
    ) as dst:
        dst.write(slope, 1)
    return out_file


def steep_areas(slope_file: str | Path, threshold: float = 30.0, min_area_m2: float = 10_000):
    """Polygons (GeoDataFrame, EPSG:4326) where slope >= threshold degrees.

    Small patches under min_area_m2 are dropped; geometries lightly simplified.
    """
    import geopandas as gpd
    from rasterio.features import shapes
    from shapely.geometry import shape

    with rasterio.open(slope_file) as src:
        slope = src.read(1)
        mask = (slope >= threshold).astype("uint8")
        polygons = [
            shape(geom)
            for geom, value in shapes(mask, mask=mask.astype(bool), transform=src.transform)
            if value == 1
        ]
        gdf = gpd.GeoDataFrame(geometry=polygons, crs=src.crs)
    gdf = gdf[gdf.area >= min_area_m2].copy()
    gdf["geometry"] = gdf.simplify(15)
    gdf["area_km2"] = (gdf.area / 1e6).round(3)
    return gdf.to_crs("EPSG:4326").reset_index(drop=True)
