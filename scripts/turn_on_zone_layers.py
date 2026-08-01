# turn_on_zone_layers.py — check on the AFTER imagery pointers in selected zone cells.
#
# For each cell in CELLS, ticks the cell subgroup, the ZONES master group, and every pointer
# whose layer either streams (wms/xyz/arcgis) or has a local file present on disk. Pointers to
# rasters whose source file is missing (e.g. Maxar deliveries on the unmounted external drive)
# are left unchecked and reported. Never unchecks anything.
#
# Run inside QGIS (Python console):  exec(open('scripts/turn_on_zone_layers.py').read())
# Project is NOT saved — save when satisfied.

import os
from qgis.core import QgsProject, QgsLayerTree

CELLS = {"B7", "B8", "C7", "C8"}
ZONES_GROUP = "ZONES — AFTER imagery (index)"

proj = QgsProject.instance()
root = proj.layerTreeRoot()
home = proj.homePath() or "."

zones = root.findGroup(ZONES_GROUP)
assert zones is not None, f"group not found: {ZONES_GROUP}"
zones.setItemVisibilityChecked(True)

for sub in zones.children():
    if not QgsLayerTree.isGroup(sub):
        continue
    code = sub.name().split(" ")[0]
    if code not in CELLS:
        continue
    sub.setItemVisibilityChecked(True)
    print(f"\n{sub.name()}")
    for node in sub.children():
        if not QgsLayerTree.isLayer(node):
            continue
        lyr = node.layer()
        if lyr is None:
            print(f"  !! no layer object, skipped: {node.name()}")
            continue
        if lyr.providerType() == "gdal":
            path = lyr.source().split("|")[0]
            for pre in ("/vsizip/", "/vsigzip/"):
                if path.startswith(pre):
                    path = path[len(pre):]
            if not os.path.isabs(path):
                path = os.path.join(home, path)
            if not os.path.exists(path):
                print(f"  -- missing on disk, left off: {node.name()}")
                continue
            node.setItemVisibilityChecked(True)
            print(f"  on (local):  {node.name()}")
        else:
            node.setItemVisibilityChecked(True)
            print(f"  on (stream): {node.name()}")

iface.mapCanvas().refreshAllLayers()
print("\nDone. Project NOT saved — save when satisfied.")
