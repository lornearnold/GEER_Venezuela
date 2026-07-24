"""List every image covering the spot you're looking at, oldest first.

Run inside QGIS while zoomed in: Plugins > Python Console > Show Editor > Run.
This is the "do I have earlier or later imagery *here*?" answer, printed as a
timeline for the current canvas centre - no Layers-panel hunting.

    2026-06-25  after   la-guaira - vantor 0.42m          [loaded]
    2026-06-26  after   la-guaira - pelican 0.62m         [loaded]
  > 2026-06-27  after   la-guaira - skysat 0.66m          [VISIBLE]

'>' marks a layer currently switched on. Tweak MODE below to query the whole
visible extent instead of just the centre point.

Reads only the footprints index, so run build_footprints.py first (and again
after adding imagery). Changes nothing in the project.
"""

from __future__ import annotations

from pathlib import Path

from qgis.core import (
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.utils import iface

ROOT = Path(__file__).resolve().parents[1]
FOOTPRINTS = ROOT / "data" / "basemaps" / "imagery_footprints.geojson"

# "centre"  - imagery covering the middle of the view (precise; what you're studying)
# "extent"  - imagery touching anywhere in the view (broader; what's nearby)
MODE = "centre"


def whats_here(mode: str = MODE) -> int:
    project = QgsProject.instance()
    canvas = iface.mapCanvas()

    layer = QgsVectorLayer(str(FOOTPRINTS), "footprints (scratch)", "ogr")
    if not layer.isValid():
        print(f"Could not read {FOOTPRINTS}.\nRun build_footprints.py first.")
        return 1

    extent = canvas.extent()
    canvas_crs = canvas.mapSettings().destinationCrs()
    if canvas_crs != layer.crs():
        transform = QgsCoordinateTransform(canvas_crs, layer.crs(), project)
        extent = transform.transformBoundingBox(extent)

    if mode == "centre":
        probe = QgsGeometry.fromPointXY(QgsPointXY(extent.center()))
        where = "the centre of your view"
    else:
        probe = QgsGeometry.fromRect(extent)
        where = "anywhere in your view"

    # Which layers are switched on right now, so we can flag them.
    # Matching is by NAME because that is the only key the footprints file stores,
    # so warn if a name is ambiguous - the [VISIBLE] flags would be unreliable.
    root = project.layerTreeRoot()
    visible = set()
    seen = {}
    for map_layer in project.mapLayers().values():
        name = map_layer.name()
        seen[name] = seen.get(name, 0) + 1
        node = root.findLayer(map_layer.id())
        if node is not None and node.isVisible():
            visible.add(name)
    ambiguous = {n for n, c in seen.items() if c > 1}
    if ambiguous:
        print(f"WARNING: {len(ambiguous)} layer name(s) are duplicated in this project;")
        print("         the [VISIBLE] flags below may point at the wrong copy.")
        print("         Run inspect_project.py for details.\n")

    hits = []
    for feature in layer.getFeatures():
        if feature.geometry().intersects(probe):
            hits.append(feature)

    def day(feature) -> str:
        """ISO date string; OGR hands back a QDate, whose repr is unreadable."""
        value = feature["datetime"]
        return value.toString("yyyy-MM-dd") if hasattr(value, "toString") else str(value)

    if not hits:
        print(f"No indexed imagery covers {where}.")
        print("(Zoom to an area with coverage, or re-run build_footprints.py.)")
        return 0

    hits.sort(key=day)
    print(f"{len(hits)} image(s) covering {where}, oldest first:\n")
    for feature in hits:
        name = feature["layer_name"]
        marker = ">" if name in visible else " "
        state = "VISIBLE" if name in visible else "loaded"
        era = feature["era"] or ""
        print(f" {marker} {day(feature)}  {era:<6}  {feature['label']:<44} [{state}]")

    dates = sorted({day(f) for f in hits})
    if len(dates) > 1:
        print(f"\n{len(dates)} distinct dates here: {dates[0]} .. {dates[-1]}")
        print("Drag the Temporal Controller across that span to flip between them.")
    return 0


# No __main__ guard: the QGIS console's Run button does not set __name__ to
# "__main__", so a guarded call would silently print nothing.
whats_here()
