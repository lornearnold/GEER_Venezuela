"""Add the Waraira Repano (El Ávila) park limits to the QGIS project.

Adds data/protected/waraira_repano.geojson to the "Terrain & Geology" group as
an outline-only polygon — a reference boundary, so it must not obscure imagery
underneath. Styled as a dashed dark-green 0.7 mm line, no fill.

Run from the QGIS Python console:

    exec(open('/Users/lornearnold/GitHub/GEER_Venezuela/scripts/add_waraira_repano_layer.py').read())

Re-running replaces the existing layer rather than adding a duplicate.
Saving the project afterwards is your call (Ctrl+S) — this script does not save.
"""

from pathlib import Path

from qgis.core import (
    QgsFillSymbol,
    QgsProject,
    QgsVectorLayer,
)

REPO = Path("/Users/lornearnold/GitHub/GEER_Venezuela")
SRC = REPO / "data/protected/waraira_repano.geojson"
LAYER_NAME = "Waraira Repano (El Ávila) park limits"
GROUP_NAME = "Terrain & Geology"

project = QgsProject.instance()
root = project.layerTreeRoot()

# Drop a previous copy so re-runs don't stack duplicates.
for lyr in list(project.mapLayers().values()):
    if lyr.name() == LAYER_NAME:
        project.removeMapLayer(lyr.id())

layer = QgsVectorLayer(str(SRC), LAYER_NAME, "ogr")
if not layer.isValid():
    raise SystemExit(f"invalid layer: {SRC}")

# Outline only — this sits over imagery and must not hide it.
symbol = QgsFillSymbol.createSimple({
    "style": "no",              # no fill
    "outline_color": "20,90,50,255",
    "outline_width": "0.7",
    "outline_width_unit": "MM",
    "outline_style": "dash",
})
layer.renderer().setSymbol(symbol)
layer.setOpacity(1.0)

project.addMapLayer(layer, False)

group = root.findGroup(GROUP_NAME)
if group is None:
    group = root.insertGroup(0, GROUP_NAME)
group.insertLayer(0, layer)

print(f"added '{LAYER_NAME}' to '{GROUP_NAME}'")
print("features:", layer.featureCount())
print("extent:", layer.extent().toString(4))
print("\nProject NOT saved — press Ctrl+S if you want to keep it.")
