#!/usr/bin/env python3
"""Rebuild the Maxar visual GeoTIFFs from the raw deliveries on the external drive.

Run with QGIS's bundled Python (system GDAL 3.3 lacks the JPEG codec):

    /Applications/QGIS.app/Contents/MacOS/python scripts/rebuild_maxar_visuals.py [scene ...]

With no arguments all six scenes are rebuilt; pass scene keys (e.g. 142038 203718)
to rebuild a subset. Each scene is written to data/imagery/maxar_visual/<name>.new.tif
and the current .tif is left untouched — QC the .new against the old at the artifact
spots, then swap manually:

    mv AFTER_x.tif AFTER_x.tif.bak && mv AFTER_x.new.tif AFTER_x.tif

(Remove the layer from QGIS before swapping a file it has open, then re-add.)

Process per scene:
1. Group the VRT's source tiles by Maxar order id (from the tile filename).
2. Sample per-band 2/98 percentiles for each order group by reading a few
   full-width row windows per tile (matches the 16384x32 strip block layout, so
   only ~1 GB is read per scene instead of the full ~100 GB).
3. If a scene mixes orders (la-guaira-west 142038: R2C04-07 recovered from order
   200013362902), rewrite the minority sources as ComplexSource with a linear
   ScaleRatio/ScaleOffset that maps their percentiles onto the primary order's,
   so one stretch serves the whole mosaic without a seam.
   WARNING (2026-09-02): percentile mapping between order groups is unreliable
   when a group has few tiles — scene content (clouds) biases the percentiles.
   For 142038 it produced a 0.42x darkening where raw edge medians showed the
   orders differ by only ~6%; the shipped 142038 visual was instead built with
   per-band ScaleRatios (1.064/1.061/1.057) measured on adjacent tile edges
   (R2C03 right edge vs R2C04 left edge). Prefer edge-median ratios over
   percentile mapping for any future cross-order normalization.
4. gdal_translate bands 5/3/2 (WV Multi-8 R/G/B; GDAL's ColorInterp tags are
   wrong) with the primary-order percentile stretch to 1-255, nodata 0, JPEG
   quality 92, YCbCr, 512px tiles; then averaged JPEG overviews.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
from osgeo import gdal

gdal.UseExceptions()

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VRT_DIR = os.path.join(REPO, "data", "imagery", "maxar_external")
OUT_DIR = os.path.join(REPO, "data", "imagery", "maxar_visual")

# band 5=Red, 3=Green, 2=Blue in WV Multi-8 deliveries
RGB_BANDS = (5, 3, 2)
PCT = (2.0, 98.0)
JPEG_QUALITY = "92"
WINDOW_ROWS = 512          # rows per sample window (multiple of the 32-row strips)
WINDOWS_PER_TILE = 3
MAX_TILES_PER_GROUP = 8

SCENES = {
    "212928": ("S2AS_362857_26JUN25.vrt", "AFTER_la-guaira_wv2_20260625_212928"),
    "212947": ("S2AS_362935_26JUN25.vrt", "AFTER_la-guaira_wv2_20260625_212947"),
    "142038": ("S2AS_366001_26JUN25.vrt", "AFTER_la-guaira-west_wv2_20260625_142038"),
    "140331": ("S2AS_365952_26JUN26.vrt", "AFTER_valencia-west_wv2_20260626_140331"),
    "140407": ("S3DS_365925_26JUN26.vrt", "AFTER_valencia-west_wv3_20260626_140407"),
    "203718": ("S3DS_362958_26JUN25.vrt", "AFTER_puerto-cabello_wv3_20260625_203718"),
}

ORDER_RE = re.compile(r"-(\d{12})_\d+_P\d+\.TIF$", re.IGNORECASE)


def tile_paths(vrt_path):
    """Unique source tile paths in VRT mosaic order."""
    seen = []
    for el in ET.parse(vrt_path).getroot().iter("SourceFilename"):
        p = el.text
        if p not in seen:
            seen.append(p)
    return seen


def order_of(path):
    m = ORDER_RE.search(os.path.basename(path))
    return m.group(1) if m else "unknown"


def sample_percentiles(paths):
    """Per-band {band: (lo, hi)} sampled from full-width row windows."""
    samples = {b: [] for b in RGB_BANDS}
    for p in paths[:MAX_TILES_PER_GROUP]:
        ds = gdal.Open(p)
        ys = ds.RasterYSize
        offsets = [int(ys * f) for f in (0.15, 0.5, 0.85)][:WINDOWS_PER_TILE]
        for y0 in offsets:
            rows = min(WINDOW_ROWS, ys - y0)
            for b in RGB_BANDS:
                arr = ds.GetRasterBand(b).ReadAsArray(0, y0, ds.RasterXSize, rows)
                vals = arr[arr > 0]
                if vals.size:
                    samples[b].append(vals)
        ds = None
    out = {}
    for b in RGB_BANDS:
        allv = np.concatenate(samples[b])
        out[b] = tuple(float(np.percentile(allv, q)) for q in PCT)
    return out


def normalized_vrt(vrt_path, primary, pct_by_order, tmp_path):
    """Copy the VRT, scaling non-primary sources onto the primary radiometry."""
    tree = ET.parse(vrt_path)
    n_scaled = 0
    for band_el in tree.getroot().iter("VRTRasterBand"):
        band = int(band_el.get("band"))
        for src in list(band_el):
            if src.tag != "SimpleSource":
                continue
            path = src.find("SourceFilename").text
            order = order_of(path)
            if order == primary or band not in RGB_BANDS:
                continue
            p2p, p98p = pct_by_order[primary][band]
            p2s, p98s = pct_by_order[order][band]
            ratio = (p98p - p2p) / (p98s - p2s)
            offset = p2p - p2s * ratio
            src.tag = "ComplexSource"
            ET.SubElement(src, "ScaleRatio").text = f"{ratio:.6f}"
            ET.SubElement(src, "ScaleOffset").text = f"{offset:.3f}"
            n_scaled += 1
    tree.write(tmp_path)
    return n_scaled


def rebuild(key):
    vrt_name, out_name = SCENES[key]
    vrt_path = os.path.join(VRT_DIR, vrt_name)
    out_path = os.path.join(OUT_DIR, out_name + ".new.tif")
    part_path = os.path.join(OUT_DIR, out_name + ".part.tif")
    if os.path.exists(out_path):
        print(f"[{key}] {os.path.basename(out_path)} exists — skipping (delete to redo)")
        return
    if os.path.exists(part_path):
        print(f"[{key}] removing stale interrupted build {os.path.basename(part_path)}")
        os.remove(part_path)

    paths = tile_paths(vrt_path)
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        sys.exit(f"[{key}] {len(missing)} source tiles not found (drive mounted?): {missing[0]}")

    groups = {}
    for p in paths:
        groups.setdefault(order_of(p), []).append(p)
    primary = max(groups, key=lambda o: len(groups[o]))
    print(f"[{key}] {len(paths)} tiles, orders: " +
          ", ".join(f"{o} x{len(ps)}" for o, ps in groups.items()) + f" (primary {primary})")

    pct_by_order = {}
    for order, ps in groups.items():
        pct_by_order[order] = sample_percentiles(ps)
        print(f"[{key}]   {order} p2/p98: " +
              " ".join(f"b{b}={v[0]:.0f}/{v[1]:.0f}" for b, v in pct_by_order[order].items()))

    src = vrt_path
    if len(groups) > 1:
        src = os.path.join(OUT_DIR, f".{key}_normalized.vrt")
        n = normalized_vrt(vrt_path, primary, pct_by_order, src)
        print(f"[{key}]   normalized {n} band-sources from secondary orders")

    # Stage 1: lossless intermediate (scaled 1-255, 0 = empty). JPEG must not be
    # the stage that defines validity: with nodata-by-value alone, decode jitter
    # punches holes and strip edges fringe (the old 142038 bug).
    # Zero-safety: raw 0 must map below 0.5 so off-strip fill stays 0 and the
    # stage-2 nodata test sees it. With src_min too low (dark scenes can sample
    # p2=1), raw 0 rounds to 1 and the mask silently ends up all-valid (caught
    # on 212947, 2026-09-02) — so floor src_min at src_max/500.
    scale = []
    for b in RGB_BANDS:
        lo, hi = pct_by_order[primary][b]
        lo = max(lo, hi / 500.0)
        scale.append([lo, hi, 1, 255])
    interm = os.path.join(OUT_DIR, f".{key}_interm.tif")
    print(f"[{key}] stage 1: lossless intermediate (long: reads the full scene)")
    gdal.Translate(
        interm, src, bandList=list(RGB_BANDS), outputType=gdal.GDT_Byte,
        scaleParams=scale, noData=0,
        creationOptions=["TILED=YES", "COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=IF_SAFER"],
        callback=gdal.TermProgress_nocb)

    # Stage 2: JPEG final with an internal mask from the data footprint.
    # NB: gdalbuildvrt -addAlpha marks mosaic COVERAGE, not nodata — it yields an
    # all-255 alpha for a single full-grid input (bug caught 2026-09-02). Warp with
    # dstAlpha + srcNodata instead, and unset NoData on the final so the mask is
    # the only transparency mechanism (NoData=0 would re-punch value holes).
    print(f"[{key}] stage 2: alpha from nodata (warp)")
    rgba = os.path.join(OUT_DIR, f".{key}_rgba.tif")
    gdal.Warp(rgba, interm, srcNodata=0, dstAlpha=True,
              creationOptions=["TILED=YES", "COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=IF_SAFER"],
              callback=gdal.TermProgress_nocb)
    print(f"[{key}] stage 2: JPEG final with internal mask")
    gdal.SetConfigOption("GDAL_TIFF_INTERNAL_MASK", "YES")
    gdal.Translate(
        part_path, rgba, bandList=[1, 2, 3], maskBand=4, noData="none",
        creationOptions=["TILED=YES", "BLOCKXSIZE=512", "BLOCKYSIZE=512",
                         "COMPRESS=JPEG", f"JPEG_QUALITY={JPEG_QUALITY}",
                         "PHOTOMETRIC=YCBCR", "BIGTIFF=IF_SAFER"],
        callback=gdal.TermProgress_nocb)

    print(f"[{key}] building overviews")
    for k, v in [("COMPRESS_OVERVIEW", "JPEG"), ("PHOTOMETRIC_OVERVIEW", "YCBCR"),
                 ("INTERLEAVE_OVERVIEW", "PIXEL"), ("JPEG_QUALITY_OVERVIEW", JPEG_QUALITY)]:
        gdal.SetConfigOption(k, v)
    ds = gdal.Open(part_path, gdal.GA_Update)
    ds.BuildOverviews("AVERAGE", [2, 4, 8, 16, 32, 64], callback=gdal.TermProgress_nocb)
    ds = None
    os.replace(part_path, out_path)
    for tmp in (interm, rgba):
        if os.path.exists(tmp):
            os.remove(tmp)
    if src != vrt_path:
        os.remove(src)
    print(f"[{key}] done: {out_path} ({os.path.getsize(out_path)/1e9:.2f} GB)")


if __name__ == "__main__":
    keys = sys.argv[1:] or list(SCENES)
    bad = [k for k in keys if k not in SCENES]
    if bad:
        sys.exit(f"unknown scene keys {bad}; choose from {list(SCENES)}")
    for k in keys:
        rebuild(k)
    print("\nAll requested scenes built as .new.tif — QC, then swap (see docstring).")
