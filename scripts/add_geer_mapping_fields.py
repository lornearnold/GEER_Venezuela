"""Add GeoSyntec-compatible attribute fields to the geer_mapping line layer.

Run from the QGIS Python console (with geer_venezuela.qgz open):

    exec(open('/Users/lornearnold/GitHub/GEER_Venezuela/scripts/add_geer_mapping_fields.py').read())

What it does
------------
1. Adds these fields to geer_mapping (names/types match the "GeoSyntec
   geomorph aerials (2026-07-20)" polygon layer; skips any that already exist):
       Confidence, Type, Comments, Source, Access, Impact  -> String
       Latitude, Longitude                                 -> Real (double)
2. Configures edit widgets on the layer:
       Confidence, Type   -> dropdown (ValueMap) with the vocabulary used in
                             the GeoSyntec layer
       Access, Impact     -> dropdown (ValueMap) with vocabularies curated
                             from GeoSyntec's actual entries (typos removed)
       Comments, Source   -> multiline text
       Latitude/Longitude -> auto-filled from the line's centroid whenever a
                             feature is created or its geometry edited
3. Backfills Latitude/Longitude for existing features that have them empty
   (set BACKFILL_LATLON = False below to skip).

The widget/default-value config lives in the project file — save the project
(Ctrl+S) afterwards to keep it. The new fields themselves are written straight
into geer_mapping.gpkg by this script.
"""

from qgis.core import (
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsField,
    QgsProject,
)
from qgis.PyQt.QtCore import QVariant

BACKFILL_LATLON = True
LAYER_NAME = "geer_mapping"

layers = QgsProject.instance().mapLayersByName(LAYER_NAME)
if not layers:
    raise RuntimeError(f"Layer '{LAYER_NAME}' not found in the project")
lyr = layers[0]
if lyr.isEditable():
    raise RuntimeError(
        f"'{LAYER_NAME}' is in an edit session — commit or roll back edits first"
    )

# --- 1. add missing fields (same names/types as the GeoSyntec polygon layer) ---
wanted = [
    QgsField("Confidence", QVariant.String),
    QgsField("Type", QVariant.String),
    QgsField("Comments", QVariant.String),
    QgsField("Source", QVariant.String),
    QgsField("Access", QVariant.String),
    QgsField("Impact", QVariant.String),
    QgsField("Latitude", QVariant.Double),
    QgsField("Longitude", QVariant.Double),
]
existing = {f.name() for f in lyr.fields()}
to_add = [f for f in wanted if f.name() not in existing]
if to_add:
    if not lyr.dataProvider().addAttributes(to_add):
        raise RuntimeError(f"Provider refused to add fields: {lyr.dataProvider().error().message()}")
    lyr.updateFields()
print(f"Added fields: {[f.name() for f in to_add] or 'none (all present already)'}")

# --- 2. edit widgets (project-level config; save the project to keep) ---
def value_map(values):
    return QgsEditorWidgetSetup("ValueMap", {"map": [{v: v} for v in values]})

# Access/Impact vocabularies are curated from how GeoSyntec actually filled the
# fields (typos dropped, near-duplicates merged). Extend by editing these lists
# and re-running, or in Layer Properties -> Attributes Form. Nuance beyond one
# category (e.g. "uphill housing and downhill road") goes in Comments.
widgets = {
    "Confidence": value_map(["Likely", "Possible", "Questionable"]),
    "Type": value_map(["Ground Rupture", "Ground Settlement", "Landslide", "Liquefaction"]),
    "Access": value_map([
        "From road",
        "From small road",
        "From trail",
        "From airport",
        "Hard",
        "Unknown",
    ]),
    "Impact": value_map([
        "None apparent",
        "Main road",
        "Small road",
        "Critical transportation route",
        "Nearby buildings",
        "Uphill buildings/housing",
        "Downhill buildings/yard",
        "Small community",
        "Airport",
        "Port",
        "Drainage/watershed",
        "Potential scientific interest",
    ]),
    "Comments": QgsEditorWidgetSetup("TextEdit", {"IsMultiline": True, "UseHtml": False}),
    "Source": QgsEditorWidgetSetup("TextEdit", {"IsMultiline": True, "UseHtml": False}),
}
flds = lyr.fields()
for name, setup in widgets.items():
    lyr.setEditorWidgetSetup(flds.indexOf(name), setup)

# Auto-fill centroid coords on create and on geometry edit (layer is EPSG:4326).
lyr.setDefaultValueDefinition(flds.indexOf("Latitude"), QgsDefaultValue("y(centroid($geometry))", True))
lyr.setDefaultValueDefinition(flds.indexOf("Longitude"), QgsDefaultValue("x(centroid($geometry))", True))
print("Widgets configured (dropdowns for Confidence/Type, autocomplete for Access/Impact).")

# --- 3. backfill Latitude/Longitude on existing features -----------------------
if BACKFILL_LATLON:
    lat_i, lon_i = flds.indexOf("Latitude"), flds.indexOf("Longitude")
    changes = {}
    for feat in lyr.getFeatures():
        if feat[lat_i] in (None,) or feat[lon_i] in (None,) or str(feat[lat_i]) == "NULL":
            g = feat.geometry()
            if g and not g.isEmpty():
                c = g.centroid().asPoint()
                changes[feat.id()] = {lat_i: c.y(), lon_i: c.x()}
    if changes:
        if not lyr.dataProvider().changeAttributeValues(changes):
            raise RuntimeError("Backfill failed: " + lyr.dataProvider().error().message())
        lyr.reload()
    print(f"Backfilled Latitude/Longitude on {len(changes)} features.")

print("Done. Save the project (Ctrl+S) to keep the widget configuration.")
