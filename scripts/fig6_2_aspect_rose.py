#!/usr/bin/env python
"""Fig. 6.2 — landslide aspect rose, by count.

Combines the two landslide inventories for §6.2 into one polar rose:

  * GeoSyntec geomorphic-interpretation polygons (Type == "Landslide"); and
  * GEER-mapped landslide lines (Candidates / geer_mapping).

Neither dataset is expected to carry slope/aspect attributes — everything is
computed here, at run time, from the DEMs in data/terrain/*_dem.tif (each
warped to UTM 19N, Horn-style gradient, cells flatter than 2° excluded):

  * polygons: circular mean of DEM aspect over the cells inside each polygon
    (representative-point sample if a polygon contains no cell center);
  * lines: circular mean of samples taken every ~15 m along each line.

Each feature is sampled from whichever DEM covers it, so new mapping areas
only need a new DEM fetched via geer_venezuela.terrain.fetch_dem().

Because the two datasets are different geometry types, each feature counts
as 1 (no area/length weighting); the two inventories are pooled. Petals are
stacked by each feature's maximum slope, binned like the exploration
notebooks (0-20-30-40-50-90 degrees) and colored with a light-to-dark
single-hue ramp. Sector binning also matches the notebooks (16 sectors,
sector 0 centered on north). Arial throughout.

Run from the repo root:

    uv run python scripts/fig6_2_aspect_rose.py
    uv run python scripts/fig6_2_aspect_rose.py --out path/to/fig.png --sectors 16

Reads only; safe to run while QGIS has the project open.
"""

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import shapely
from rasterio.warp import Resampling, calculate_default_transform, reproject

REPO = Path(__file__).resolve().parents[1]

GEOSYNTEC = REPO / "data/geosyntec/geosyntec_geomorph_aerials_20260720.geojson"
GEER_LINES = REPO / "data/landslide_candidates/geer_mapping.gpkg"
DEM_GLOB = "*_dem.tif"
DEM_DIR = REPO / "data/terrain"
OUT_DEFAULT = REPO / "06_Landslides/fig6_2_rose_count.png"

UTM = "EPSG:32619"  # UTM 19N — same working CRS as the notebooks
SAMPLE_SPACING_M = 15.0  # ~half the ~30 m DEM cell size
MIN_SLOPE_DEG = 2.0  # cells flatter than this have no meaningful aspect

# Max-slope classes, same as the notebooks' SLOPE_BINS = [0, 20, 30, 40, 50, 90].
SLOPE_BINS = [0, 20, 30, 40, 50, 90]
SLOPE_LABELS = ["0–20°", "20–30°", "30–40°", "40–50°", ">50°"]
# Sequential single-hue ramp (light → dark = gentle → steep), ColorBrewer Blues.
SLOPE_COLORS = ["#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c"]

plt.rcParams["font.family"] = ["Arial", "Helvetica", "sans-serif"]


def dem_aspect_utm(dem_path):
    """Warp a DEM to UTM 19N and return (aspect_deg, slope_deg, transform).

    Aspect is the downslope azimuth in degrees clockwise from north.
    """
    with rasterio.open(dem_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, UTM, src.width, src.height, *src.bounds
        )
        z = np.full((height, width), np.nan, dtype="float32")
        reproject(
            source=rasterio.band(src, 1),
            destination=z,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=UTM,
            resampling=Resampling.bilinear,
            dst_nodata=np.nan,
        )

    xres = transform.a
    yres = -transform.e  # positive cell height in meters
    # Gradient: axis 0 is rows (southward in a north-up raster), axis 1 is cols.
    dzdy_rows, dzdx = np.gradient(z, yres, xres)
    dzdy = -dzdy_rows  # positive = elevation increases northward
    # Downslope vector is -grad(z); azimuth measured clockwise from north.
    aspect = (np.degrees(np.arctan2(-dzdx, -dzdy))) % 360.0
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    # Sea / no-data: these DEMs have no nodata tag; treat elevation <= 0 as invalid.
    invalid = ~np.isfinite(z) | (z <= 0)
    aspect[invalid] = np.nan
    slope[invalid] = np.nan
    return aspect, slope, transform


def load_grids():
    """Aspect/slope grids for every *_dem.tif in data/terrain."""
    dem_paths = sorted(DEM_DIR.glob(DEM_GLOB))
    if not dem_paths:
        raise SystemExit(f"no DEMs matching {DEM_GLOB} in {DEM_DIR}")
    grids = []
    for p in dem_paths:
        aspect, slope, transform = dem_aspect_utm(p)
        grids.append((p.name, aspect, slope, transform))
    return grids


def valid_samples_at(grids, xs, ys):
    """DEM (aspect, slope) samples at UTM points (xs, ys).

    Each point takes its values from the first grid that covers it. Aspect
    samples are slope-filtered (>= MIN_SLOPE_DEG); slope samples are not, so
    the per-feature max slope sees every covered cell.
    """
    aspect_samples, slope_samples = [], []
    for x, y in zip(xs, ys):
        for _, aspect, slope, transform in grids:
            col, row = ~transform * (x, y)
            r, c = int(row), int(col)
            if 0 <= r < aspect.shape[0] and 0 <= c < aspect.shape[1] \
                    and np.isfinite(aspect[r, c]):
                slope_samples.append(slope[r, c])
                if slope[r, c] >= MIN_SLOPE_DEG:
                    aspect_samples.append(aspect[r, c])
                break  # covered by this DEM; don't double-sample
    return aspect_samples, slope_samples


def circular_mean_deg(angles_deg):
    a = np.radians(np.asarray(angles_deg, dtype=float))
    s, c = np.sin(a).mean(), np.cos(a).mean()
    return float(np.degrees(np.arctan2(s, c)) % 360.0)


def line_sample_points(geom, spacing=SAMPLE_SPACING_M):
    """Points every `spacing` meters along a (Multi)LineString (UTM coords)."""
    parts = getattr(geom, "geoms", [geom])
    xs, ys = [], []
    for part in parts:
        n = max(int(np.ceil(part.length / spacing)), 1) + 1
        for d in np.linspace(0.0, part.length, n):
            p = part.interpolate(d)
            xs.append(p.x)
            ys.append(p.y)
    return xs, ys


def polygon_cell_centers(geom, grids):
    """Centers of DEM cells inside a polygon (first covering grid's lattice)."""
    minx, miny, maxx, maxy = geom.bounds
    for _, aspect, _, transform in grids:
        c0, r1 = ~transform * (minx, miny)
        c1, r0 = ~transform * (maxx, maxy)
        r0, r1 = int(np.floor(r0)), int(np.ceil(r1))
        c0, c1 = int(np.floor(c0)), int(np.ceil(c1))
        h, w = aspect.shape
        if r1 < 0 or r0 >= h or c1 < 0 or c0 >= w:
            continue  # bbox entirely outside this grid
        rows = np.arange(max(r0, 0), min(r1 + 1, h))
        cols = np.arange(max(c0, 0), min(c1 + 1, w))
        if not len(rows) or not len(cols):
            continue
        cc, rr = np.meshgrid(cols, rows)
        xs, ys = transform * (cc.ravel() + 0.5, rr.ravel() + 0.5)
        inside = shapely.contains_xy(geom, xs, ys)
        if inside.any():
            return list(xs[inside]), list(ys[inside])
    # Tiny polygon (no cell center inside): fall back to a single point.
    p = geom.representative_point()
    return [p.x], [p.y]


def feature_aspects(gdf, grids, kind):
    """Per-feature (circular-mean aspect, max slope); NaN where no samples."""
    asp = np.full(len(gdf), np.nan)
    smax = np.full(len(gdf), np.nan)
    utm = gdf.to_crs(UTM)
    for i, geom in enumerate(utm.geometry):
        if kind == "line":
            xs, ys = line_sample_points(geom)
        else:
            xs, ys = polygon_cell_centers(geom, grids)
        aspect_samples, slope_samples = valid_samples_at(grids, xs, ys)
        if aspect_samples:
            asp[i] = circular_mean_deg(aspect_samples)
        if slope_samples:
            smax[i] = max(slope_samples)
    return asp, smax


def sectorize(aspect_deg, n_sectors):
    """Sector index with sector 0 centered on north (matches the notebooks)."""
    width = 360.0 / n_sectors
    return np.floor(((np.asarray(aspect_deg) + width / 2) % 360.0) / width).astype(int)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--sectors", type=int, default=16)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    grids = load_grids()
    print("DEMs:", ", ".join(name for name, *_ in grids))

    # --- GeoSyntec polygons -------------------------------------------------
    gs = gpd.read_file(GEOSYNTEC)
    gs = gs[gs.Type == "Landslide"]
    poly_asp, poly_smax = feature_aspects(gs, grids, "polygon")

    # --- GEER-mapped lines ---------------------------------------------------
    lines = gpd.read_file(GEER_LINES, layer="geer_mapping")
    line_asp, line_smax = feature_aspects(lines, grids, "line")

    # --- Pool the two inventories (count each feature once) ------------------
    asp = np.concatenate([poly_asp, line_asp])
    smax = np.concatenate([poly_smax, line_smax])
    ok = ~np.isnan(asp) & ~np.isnan(smax)
    n_dropped = int((~ok).sum())
    asp, smax = asp[ok], smax[ok]

    n_poly_ok = int((~np.isnan(poly_asp) & ~np.isnan(poly_smax)).sum())
    n_line_ok = int((~np.isnan(line_asp) & ~np.isnan(line_smax)).sum())
    print(f"GeoSyntec landslide polygons: {n_poly_ok}")
    print(f"GEER-mapped lines: {n_line_ok}")
    if n_dropped:
        print(f"dropped {n_dropped} feature(s): flat or no DEM coverage")

    # --- Bin: sector x max-slope class ---------------------------------------
    n = args.sectors
    sectors = sectorize(asp, n)
    sbin = np.digitize(smax, SLOPE_BINS[1:-1])  # 0..4, same as the notebooks
    n_classes = len(SLOPE_LABELS)
    counts = np.zeros((n_classes, n), dtype=int)
    for k in range(n_classes):
        counts[k] = np.bincount(sectors[sbin == k], minlength=n)

    # --- Console summary -----------------------------------------------------
    labels16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    print("max-slope class totals: "
          + ", ".join(f"{lab} {counts[k].sum()}" for k, lab in enumerate(SLOPE_LABELS)))
    if n == 16:
        header = " ".join(f"{lab:>7}" for lab in SLOPE_LABELS)
        print(f"{'sector':>6} {header} {'total':>6}")
        for j in range(n):
            row = " ".join(f"{counts[k, j]:>7}" for k in range(n_classes))
            print(f"{labels16[j]:>6} {row} {counts[:, j].sum():>6}")

    # --- Rose ----------------------------------------------------------------
    theta = np.arange(n) * (2 * np.pi / n)
    width = 2 * np.pi / n * 0.95  # small gap between petals

    fig = plt.figure(figsize=(6.5, 6.5))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    bottom = np.zeros(n)
    for k in range(n_classes):
        ax.bar(theta, counts[k], width=width, bottom=bottom,
               color=SLOPE_COLORS[k], edgecolor="white", linewidth=1.2,
               label=SLOPE_LABELS[k])
        bottom += counts[k]

    if n == 16:
        ax.set_xticks(theta)
        ax.set_xticklabels([lab if lab in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
                            else "" for lab in labels16], fontsize=11)
    ax.tick_params(axis="y", labelsize=9, colors="0.4")
    ax.yaxis.grid(True, color="0.85", linewidth=0.8)
    ax.xaxis.grid(True, color="0.85", linewidth=0.8)
    ax.spines["polar"].set_color("0.7")
    ax.set_rlabel_position(200)
    ax.legend(title="Max slope", loc="upper left", bbox_to_anchor=(-0.12, 1.10),
              frameon=False, fontsize=10, title_fontsize=10)

    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, bbox_inches="tight")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
