"""Toolbar button: stamp geer_mapping's Source field from an imagery layer.

Run from the QGIS Python console (safe to re-run; replaces the old button):

    exec(open('/Users/lornearnold/GitHub/GEER_Venezuela/scripts/source_stamp_button.py').read())

Adds a "Stamp Source" button to the toolbar. Workflow:

  1. In the Layers panel, click the imagery layer you are tracing from
     (any raster — AFTER, BEFORE, or NASA; a ZONES pointer node works too).
  2. Press the button. It:
       - builds a source string from the layer's actual data source:
           Vantor stream  -> the COG URL (…vantor-opendata.s3.amazonaws.com/….tif)
           NASA / XYZ     -> the service URL
           Wayback (TMS)  -> the tile ServerUrl from the GDAL_WMS XML
           local Planet   -> "Planet SkySat|Pelican ortho_visual <item id>"
           local Maxar    -> "Maxar WorldView-2|3 scene <scene_id>" (from
                             maxar_footprints.geojson)
           local Vantor   -> mosaic-source scene IDs + S3 prefix (from
                             vantor_opendata_footprints.geojson)
           other local    -> path relative to the repo
       - stores it in the project variable @mapping_source,
       - sets geer_mapping's Source default value to @mapping_source, so every
         feature you digitize from now on is stamped automatically,
       - if geer_mapping is IN EDIT MODE with features selected, also writes
         the string to those features' Source (undoable; you commit).
  3. Digitize. Press the button again whenever you switch imagery layers.

The button lives only for this QGIS session — re-run the exec line after a
restart (or call it from your profile's python/startup.py). The default-value
expression and @mapping_source persist in the project once you save it.
"""

import json
import os
import re
from urllib.parse import unquote

from qgis.core import (
    QgsDefaultValue,
    QgsExpressionContextUtils,
    QgsMapLayer,
    QgsProject,
)
from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface

ACTION_NAME = "geer_stamp_source"
LAYER_NAME = "geer_mapping"


_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _repo_root():
    home = QgsProject.instance().homePath()  # .../GEER_Venezuela/qgis
    return os.path.dirname(home) if home else ""


def _manifest_features(rel_path):
    path = os.path.join(_repo_root(), rel_path)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f).get("features", [])


def _local_reference(src):
    """Provider-catalog reference for a locally cached file; None if unknown."""
    base = os.path.basename(src)

    # Planet visual products: the filename embeds the collect/item ID
    m = re.match(r"(skysat|pelican)_(\d{8}_\d{6}_\w+?)_visual\.tif$", base)
    if m:
        family = {"skysat": "SkySat", "pelican": "Pelican"}[m.group(1)]
        return f"Planet {family} ortho_visual {m.group(2)}"

    # Maxar visual GeoTIFFs: look up the delivery scene_id in the manifest
    m = re.match(r"AFTER_.+_(wv\d)_(\d{4})(\d{2})(\d{2})_(\d{6})\.tif$", base)
    if m:
        wv, yyyy, mo, dd, hhmmss = m.groups()
        date_key = f"{yyyy[2:]}{_MONTHS[int(mo) - 1]}{dd}"  # 2026-06-25 -> 26JUN25
        sensors = {"S2AS": "WorldView-2", "S3DS": "WorldView-3"}
        for ft in _manifest_features("data/basemaps/maxar_visual/maxar_footprints.geojson"):
            p = ft.get("properties", {})
            if p.get("date") == date_key and p.get("time_z") == hhmmss:
                name = sensors.get(p.get("sensor"), {"wv2": "WorldView-2", "wv3": "WorldView-3"}[wv])
                return f"Maxar {name} scene {p['scene_id']}"
        return None

    # Locally built Vantor mosaic: list the source scenes + their S3 prefix
    if base.startswith("vantor_") and "mosaic" in base:
        feats = _manifest_features("data/basemaps/vantor_opendata_footprints.geojson")
        srcs = [f["properties"] for f in feats
                if f.get("properties", {}).get("holding") == "mosaic-source"]
        if srcs:
            ids = ", ".join(p["scene_id"] for p in srcs)
            prefix = srcs[0].get("url", "").rsplit("/", 1)[0] + "/"
            return f"Vantor Legion mosaic of scenes {ids} @ {prefix}"

    return None


def _source_string(layer):
    """Resolve the layer's actual data source to a stampable URI/path."""
    src = layer.source()

    # Vantor/remote COGs: /vsicurl/https://… -> plain URL
    if src.startswith("/vsicurl/"):
        return src[len("/vsicurl/"):]

    # Wayback etc.: GDAL_WMS XML, inline or as a file -> tile ServerUrl
    xml = src
    if src.lower().endswith(".xml") and os.path.exists(src):
        with open(src) as f:
            xml = f.read()
    m = re.search(r"<ServerUrl>\s*([^<]+?)\s*</ServerUrl>", xml)
    if m:
        return m.group(1)

    # NASA ImageServer / WMS-style connection strings: url='…' or url=…&
    m = re.search(r"url='([^']+)'", src) or re.search(r"url=([^&]+)", src)
    if m:
        return unquote(m.group(1))

    # Local files: prefer a provider-catalog reference from the manifests;
    # fall back to a repo-relative path (project home is qgis/, so also try
    # its parent, the repo root).
    if os.path.isabs(src):
        ref = _local_reference(src)
        if ref:
            return ref
        home = QgsProject.instance().homePath()
        for base in filter(None, [home, os.path.dirname(home) if home else None]):
            if src.startswith(base + os.sep):
                return os.path.relpath(src, base)
        return src

    # Fallback: whatever QGIS reports, better than nothing
    return src


def _stamp():
    proj = QgsProject.instance()
    img = iface.activeLayer()
    if img is None or img.type() != QgsMapLayer.RasterLayer:
        iface.messageBar().pushWarning(
            "Stamp Source", "Click an imagery (raster) layer in the Layers panel first."
        )
        return
    src = _source_string(img)

    # 1. project variable -> picked up by the default value on new features
    QgsExpressionContextUtils.setProjectVariable(proj, "mapping_source", src)

    # 2. make sure geer_mapping's Source default is wired to it
    gm_layers = proj.mapLayersByName(LAYER_NAME)
    if not gm_layers:
        iface.messageBar().pushWarning("Stamp Source", f"Layer '{LAYER_NAME}' not found.")
        return
    gm = gm_layers[0]
    src_idx = gm.fields().indexOf("Source")
    if src_idx < 0:
        iface.messageBar().pushWarning("Stamp Source", "geer_mapping has no Source field.")
        return
    if gm.defaultValueDefinition(src_idx).expression() != "@mapping_source":
        gm.setDefaultValueDefinition(src_idx, QgsDefaultValue("@mapping_source", False))

    # 3. optionally stamp the current selection (only inside an edit session,
    #    so it stays undoable and committing is your call)
    n_sel = gm.selectedFeatureCount()
    stamped = 0
    if n_sel and gm.isEditable():
        gm.beginEditCommand("Stamp Source on selection")
        for fid in gm.selectedFeatureIds():
            gm.changeAttributeValue(fid, src_idx, src)
            stamped += 1
        gm.endEditCommand()
    note = f" · stamped {stamped} selected feature(s)" if stamped else (
        f" · {n_sel} selected but layer not in edit mode — toggle editing to stamp them"
        if n_sel else ""
    )
    iface.messageBar().pushSuccess("Stamp Source", f"New features get: “{src}”{note}")


# (re)install the toolbar button
for tb_action in iface.mainWindow().findChildren(QAction, ACTION_NAME):
    iface.removeToolBarIcon(tb_action)
    tb_action.deleteLater()

_action = QAction("Stamp Source", iface.mainWindow())
_action.setObjectName(ACTION_NAME)
_action.setToolTip("Set geer_mapping Source from the active imagery layer")
_action.triggered.connect(_stamp)
iface.addToolBarIcon(_action)
print("“Stamp Source” button added to the toolbar. Click an imagery layer, press it, digitize.")
