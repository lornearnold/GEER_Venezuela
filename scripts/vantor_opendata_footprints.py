#!/usr/bin/env python3
"""Build a footprint GeoJSON of the Vantor Open Data collection for this event.

Fetches the STAC collection + all items from the public S3 bucket and writes
data/basemaps/vantor_opendata_footprints.geojson with one polygon per scene,
carrying the attributes needed to browse coverage in QGIS (Temporal Controller
compatible: `datetime`/`era` like imagery_footprints.geojson) plus a ready-made
`vsicurl` URI so any scene can be streamed without downloading:

    Add Raster Layer -> paste the feature's `vsicurl` value.

Stdlib only; safe to re-run (overwrites the output). Remove the layer from QGIS
before re-running (see CLAUDE.md gotcha about QGIS flushing cached copies).

Usage: python3 scripts/vantor_opendata_footprints.py
"""

import json
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:  # macOS framework Python ships without a CA bundle
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

COLLECTION = (
    "https://vantor-opendata.s3.amazonaws.com/events/"
    "Venezuela-Earthquake-Jun-2026/collection.json"
)
OUT = Path(__file__).resolve().parent.parent / "data/basemaps/vantor_opendata_footprints.geojson"

SENSOR_NAMES = {"WV02": "worldview-2", "WV03": "worldview-3", "GE01": "geoeye-1"}

# Scenes already held locally in some form (see PROGRESS.md 2026-07-24 entry).
DELIVERED = {"B16000110179D310", "B16000110179D410"}  # = maxar_visual la-guaira 21:29 pair
MOSAIC_SOURCE = {"B110001100BB2210", "B110001100BB2310", "B110001100BB2510"}


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60, context=SSL_CTX) as r:
        return json.load(r)


def content_length(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
        return int(r.headers.get("Content-Length", 0))


def to_feature(item):
    p = item["properties"]
    sid = item["id"]
    vehicle = p.get("vehicle_name", "?")
    sensor = SENSOR_NAMES.get(vehicle, "legion")
    href = item["assets"]["visual"]["href"]
    date = p["datetime"][:10]
    era = "after" if p.get("phase") == "post" else "before"
    if sid in DELIVERED:
        holding = "delivered-scene"
    elif sid in MOSAIC_SOURCE:
        holding = "mosaic-source"
    else:
        holding = "stream-only"
    size_gb = round(content_length(href) / 1024**3, 2)
    return {
        "type": "Feature",
        "geometry": item["geometry"],
        "properties": {
            "scene_id": sid,
            "label": f"{sensor} · {p.get('pan_gsd', '?')}m · {date}",
            "datetime": date,
            "time_z": p["datetime"][11:19],
            "sensor": sensor,
            "vehicle": vehicle,
            "era": era,
            "gsd": p.get("pan_gsd"),
            "cloud_cover": p.get("eo:cloud_cover"),
            "off_nadir": p.get("view:off_nadir"),
            "size_gb": size_gb,
            "holding": holding,
            "url": href,
            "vsicurl": f"/vsicurl/{href}",
        },
    }


BUCKET_LIST = (
    "https://vantor-opendata.s3.amazonaws.com/?list-type=2"
    "&prefix=events/Venezuela-Earthquake-Jun-2026/&max-keys=1000"
)


def bucket_item_urls():
    """Every <scene>.json in the bucket, listed directly from S3.

    collection.json has been observed to be wrong (2026-08-21: one item linked twice,
    one — B040001100075810 — missing), so the bucket listing is the ground truth and
    the collection's links are only a second source.
    """
    import re
    with urllib.request.urlopen(BUCKET_LIST, timeout=60, context=SSL_CTX) as r:
        xml = r.read().decode()
    keys = re.findall(r"<Key>([^<]+\.json)</Key>", xml)
    base = "https://vantor-opendata.s3.amazonaws.com/"
    return {base + k for k in keys if not k.endswith("collection.json")}


def main():
    coll = fetch_json(COLLECTION)
    from_collection = {l["href"] for l in coll["links"] if l["rel"] == "item"}
    from_bucket = bucket_item_urls()
    item_urls = sorted(from_collection | from_bucket)
    print(f"{len(from_collection)} unique items linked from collection.json, "
          f"{len(from_bucket)} item files in the bucket -> {len(item_urls)} total")
    only_bucket = from_bucket - from_collection
    if only_bucket:
        print("  not linked from collection.json:", sorted(u.rsplit('/', 1)[1] for u in only_bucket))
    with ThreadPoolExecutor(max_workers=8) as pool:
        items = list(pool.map(fetch_json, item_urls))
        features = list(pool.map(to_feature, items))
    features.sort(key=lambda f: (f["properties"]["datetime"], f["properties"]["time_z"]))
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=1))
    n_after = sum(1 for f in features if f["properties"]["era"] == "after")
    print(f"wrote {OUT} ({len(features)} scenes: {n_after} post-event, "
          f"{len(features) - n_after} pre-event)")


if __name__ == "__main__":
    sys.exit(main())
