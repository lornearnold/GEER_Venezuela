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
#  - Cell codes: letter = row (A at the top, going south), number = column (1 at the west,
#    going east) — so alphabetical group order reads the map left-to-right, top-to-bottom.
#    Anchored at NW -69.0, 11.0 so codes stay stable as imagery is added.

import json, math, os, re
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsLayerTreeLayer, QgsVectorLayer, QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings,
                       QgsFillSymbol, QgsSingleSymbolRenderer)
from qgis.PyQt.QtGui import QColor, QFont

DRY_RUN = False
CELL_DEG = 0.25
ORIGIN_LON, ORIGIN_LAT = -69.0, 11.0          # NW anchor of cell "A1" — do not change once adopted
SOURCE_GROUP = "AFTER — post-event imagery"
ZONES_GROUP = "ZONES — AFTER imagery (index)"
INDEX_LAYER = "ZONE index — AFTER imagery"
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

# Hard stop on an empty/broken project state — never build empty groups or overwrite the
# index geojson with zero features (that is how a bad state propagates).
assert layers, f"no layers found under '{SOURCE_GROUP}' — aborting, nothing touched"

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
    letters = ""                      # letter = ROW (A northmost), number = COLUMN (1 westmost)
    n = ri
    while True:
        letters = chr(ord("A") + n % 26) + letters
        n = n // 26 - 1
        if n < 0:
            break
    return f"{letters}{ci + 1}"

# --- assign layers to cells ----------------------------------------------------------------
cells = {}                                              # (ci,ri) -> [(layer,bbox),...]
for lyr, bb in layers:
    c0, r1 = cell_of(bb.xMinimum(), bb.yMinimum())
    c1, r0 = cell_of(bb.xMaximum(), bb.yMaximum())
    for ci in range(c0, c1 + 1):
        for ri in range(r0, r1 + 1):
            cells.setdefault((ci, ri), []).append(lyr)

GENERIC_LOCS = {"aoi-coast", "caracas-corridor"}   # wide-footprint layers; poor cell labels

def place_of(members):
    counts = {}
    for l in members:
        counts[location_of(l.name())] = counts.get(location_of(l.name()), 0) + 1
    # a real place name beats any generic wide-footprint name, regardless of count
    ranked = sorted(counts.items(),
                    key=lambda kv: (kv[0] in GENERIC_LOCS, -kv[1], kv[0]))
    return ranked[0][0]

ordered = sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0]))   # row-major, NW first
print(f"{'DRY RUN — ' if DRY_RUN else ''}{len(layers)} AFTER layers -> {len(cells)} occupied cells "
      f"({sum(len(v) for v in cells.values())} pointers)\n")
for (ci, ri), members in ordered:
    print(f"  {cell_code(ci, ri):>4} · {place_of(members):<22} {len(members):>2} layers")

if not DRY_RUN:
    # --- (re)build the zones group ---------------------------------------------------------
    n_registry = len(proj.mapLayers())
    # Rebuild IN PLACE: keep the group's current position (and parent) in the layer tree.
    # Only a first-ever build puts it at the top.
    old = root.findGroup(ZONES_GROUP)
    parent, pos = root, 0
    if old is not None:
        parent = old.parent() or root
        pos = parent.children().index(old)
        parent.removeChildNode(old)                      # pointers only; layers survive
    zg = parent.insertGroup(pos, ZONES_GROUP)
    for (ci, ri), members in ordered:
        sub = zg.addGroup(f"{cell_code(ci, ri)} · {place_of(members)} ({len(members)})")
        for lyr in sorted(members, key=lambda l: l.name()):
            n = sub.addLayer(lyr)                        # pointer — same layer, second node
            n.setItemVisibilityChecked(False)
        sub.setExpanded(False)
    zg.setExpanded(True)
    assert len(proj.mapLayers()) == n_registry, \
        "layer registry changed while rebuilding zone groups — investigate before saving!"

    # --- (re)write + (re)add the zone index layer ------------------------------------------
    # Rebuild IN PLACE: note where the current index layer sits, and put the new one there.
    # Only a first-ever build defaults to the top of the tree.
    gj = os.path.abspath(GEOJSON)
    tgt, tpos, tvis = root, 0, True
    for l in list(proj.mapLayers().values()):            # remove BEFORE editing on disk
        if os.path.abspath(l.source().split("|")[0]) == gj:
            node = root.findLayer(l.id())
            if node is not None and node.parent() is not None:
                tgt = node.parent()
                tpos = tgt.children().index(node)
                tvis = node.itemVisibilityChecked()
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
    vl.setRenderer(QgsSingleSymbolRenderer(sym))   # don't assume a default renderer exists
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
    node = tgt.insertLayer(tpos, vl)
    node.setItemVisibilityChecked(tvis)
    print(f"\nBuilt {len(cells)} zone groups + index layer -> {gj}")
    print("Project NOT saved — save when satisfied.")
    print("Reminder: toggle pointers with checkboxes; never right-click-remove them.")
