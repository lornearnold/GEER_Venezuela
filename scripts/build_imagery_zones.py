# build_imagery_zones.py — spatial index for the AFTER imagery as layer-tree groups.
#
# Builds a "ZONES — AFTER imagery (index)" group of 0.25° (~27 km) grid cells. Each cell
# subgroup ("B3 · la-guaira (7)") holds POINTER nodes to every AFTER layer whose footprint
# intersects the cell — the same layer appears under every cell it touches. A layer renders
# when ANY of its checked pointers sits under a checked group, so ticking imagery inside the
# zone you're working lights it up regardless of the master group's checkbox.
#
# Also writes data/derived/imagery_zones.geojson and adds it as a labeled outline layer
# ("ZONE index — AFTER imagery") so the canvas shows which zone you're in.
#
# Run inside QGIS (Python console):  exec(open('scripts/build_imagery_zones.py').read())
# DRY_RUN=True prints the planned cells. Re-running rebuilds the whole index (safe: only
# pointer nodes and the index layer are replaced; the imagery layers themselves are untouched).
#
# RULES OF THE ROAD
#  - Never right-click > Remove Layer on a pointer: that removes the LAYER everywhere.
#    Rebuild with this script instead; toggle with checkboxes only.
#  - Cell codes are anchored (A1 = NW of -69.0, 11.5), so they stay stable as imagery is added.

import json, math, os, re
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsLayerTreeLayer, QgsVectorLayer, QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings,
                       QgsFillSymbol)
from qgis.PyQt.QtGui import QColor, QFont

DRY_RUN = True
CELL_DEG = 0.25
ORIGIN_LON, ORIGIN_LAT = -69.0, 11.5          # NW anchor of cell "A1" — do not change once adopted
SOURCE_GROUP = "AFTER — post-event imagery"
ZONES_GROUP = "ZONES — AFTER imagery (index)"
INDEX_LAYER = "ZONE index — AFTER imagery"
INDEX_GROUP = "Imagery footprints (toggle)"    # where the index layer goes (root if absent)
GEOJSON = os.path.join(QgsProject.instance().homePath() or ".",
                       "..", "data", "derived", "imagery_zones.geojson")

proj = QgsProject.instance()
root = proj.layerTreeRoot()
wgs = QgsCoordinateReferenceSystem("EPSG:4326")

# --- collect AFTER layers + their WGS84 bboxes ---------------------------------------------
src = root.findGroup(SOURCE_GROUP)
assert src is not None, f"group not found: {SOURCE_GROUP}"
layers = []
for node in src.findLayers():
    lyr = node.layer()
    if lyr is None:
        continue
    ext = lyr.extent()
    if ext.isEmpty():
        print(f"  !! empty extent, skipped: {lyr.name()}")
        continue
    xf = QgsCoordinateTransform(lyr.crs(), wgs, proj)
    layers.append((lyr, xf.transformBoundingBox(ext)))

def location_of(name):
    """Location token from either naming scheme."""
    toks = [t.strip() for t in name.split(" — ", 1)[-1].split(" · ")]
    if re.match(r"^\d{2}-\d{2}$|^\d{4}-\d{2}-\d{2}$", toks[0]):
        return toks[2] if len(toks) > 2 else "?"       # new: date · res sensor · LOC · id
    return toks[0]                                      # old: LOC · sensor res · id

def cell_of(lon, lat):
    return (int(math.floor((lon - ORIGIN_LON) / CELL_DEG)),
            int(math.floor((ORIGIN_LAT - lat) / CELL_DEG)))

def cell_code(ci, ri):
    letters = ""
    n = ci
    while True:
        letters = chr(ord("A") + n % 26) + letters
        n = n // 26 - 1
        if n < 0:
            break
    return f"{letters}{ri + 1}"

# --- assign layers to cells ----------------------------------------------------------------
cells = {}                                              # (ci,ri) -> [(layer,bbox),...]
for lyr, bb in layers:
    c0, r1 = cell_of(bb.xMinimum(), bb.yMinimum())
    c1, r0 = cell_of(bb.xMaximum(), bb.yMaximum())
    for ci in range(c0, c1 + 1):
        for ri in range(r0, r1 + 1):
            cells.setdefault((ci, ri), []).append(lyr)

def place_of(members):
    counts = {}
    for l in members:
        counts[location_of(l.name())] = counts.get(location_of(l.name()), 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

ordered = sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0]))   # row-major, NW first
print(f"{'DRY RUN — ' if DRY_RUN else ''}{len(layers)} AFTER layers -> {len(cells)} occupied cells "
      f"({sum(len(v) for v in cells.values())} pointers)\n")
for (ci, ri), members in ordered:
    print(f"  {cell_code(ci, ri):>4} · {place_of(members):<22} {len(members):>2} layers")

if not DRY_RUN:
    # --- (re)build the zones group ---------------------------------------------------------
    old = root.findGroup(ZONES_GROUP)
    if old is not None:
        root.removeChildNode(old)                        # pointers only; layers survive
    zg = root.insertGroup(0, ZONES_GROUP)
    for (ci, ri), members in ordered:
        sub = zg.addGroup(f"{cell_code(ci, ri)} · {place_of(members)} ({len(members)})")
        for lyr in sorted(members, key=lambda l: l.name()):
            n = sub.addLayer(lyr)                        # pointer — same layer, second node
            n.setItemVisibilityChecked(False)
        sub.setExpanded(False)
    zg.setExpanded(True)

    # --- (re)write + (re)add the zone index layer ------------------------------------------
    gj = os.path.abspath(GEOJSON)
    for l in list(proj.mapLayers().values()):            # remove BEFORE editing on disk
        if os.path.abspath(l.source().split("|")[0]) == gj:
            proj.removeMapLayer(l.id())
    os.makedirs(os.path.dirname(gj), exist_ok=True)
    feats = []
    for (ci, ri), members in ordered:
        x0 = ORIGIN_LON + ci * CELL_DEG
        y1 = ORIGIN_LAT - ri * CELL_DEG
        x1, y0 = x0 + CELL_DEG, y1 - CELL_DEG
        feats.append({"type": "Feature",
                      "properties": {"zone": cell_code(ci, ri),
                                     "place": place_of(members),
                                     "label": f"{cell_code(ci, ri)} · {place_of(members)}",
                                     "n_layers": len(members)},
                      "geometry": {"type": "Polygon",
                                   "coordinates": [[[x0, y0], [x1, y0], [x1, y1],
                                                    [x0, y1], [x0, y0]]]}})
    with open(gj, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)

    vl = QgsVectorLayer(gj, INDEX_LAYER, "ogr")
    assert vl.isValid(), "zone index geojson failed to load"
    sym = QgsFillSymbol.createSimple({"style": "no", "outline_color": "90,90,90,180",
                                      "outline_style": "dash", "outline_width": "0.6"})
    vl.renderer().setSymbol(sym)
    pal = QgsPalLayerSettings()
    pal.fieldName = "label"
    fmt = QgsTextFormat()
    fmt.setFont(QFont("Helvetica", 10, QFont.Bold))
    fmt.setColor(QColor(60, 60, 60))
    buf = QgsTextBufferSettings(); buf.setEnabled(True); buf.setSize(1.2)
    fmt.setBuffer(buf)
    pal.setFormat(fmt)
    vl.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    vl.setLabelsEnabled(True)
    proj.addMapLayer(vl, False)
    tgt = root.findGroup(INDEX_GROUP) or root
    tgt.insertLayer(0, vl)
    print(f"\nBuilt {len(cells)} zone groups + index layer -> {gj}")
    print("Project NOT saved — save when satisfied.")
    print("Reminder: toggle pointers with checkboxes; never right-click-remove them.")
