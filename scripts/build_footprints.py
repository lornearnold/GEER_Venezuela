"""Rebuild the imagery footprints index from the dated rasters in the project.

Writes one polygon per dated scene to data/basemaps/imagery_footprints.geojson,
carrying the attributes that make date-aware navigation possible:

    layer_name  exact QGIS layer name (the join key back to the raster)
    label       human-readable 'la-guaira - pelican 0.62m - 2026-06-26'
    datetime    capture date, as a real date field
    sensor, gsd, location
    era         'before' | 'after', relative to the 2026-06-24 earthquake

Run inside QGIS: Plugins > Python Console > Show Editor > open this > Run.

The footprints layer is the spatial index behind "do I have earlier or later
imagery *here*?" - zoom anywhere, and the polygons covering your view are the
answer. Style it hollow and label it by date; see scripts/README.md.

NOTE: if the footprints layer is currently loaded in QGIS, this script removes it
before writing (QGIS caches vector files and will flush its stale copy back over
an external write), then re-adds it. That reload is the only project mutation.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QDate, QVariant

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imagery_index import dated_rasters, gsd_of, location_of, sensor_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "basemaps" / "imagery_footprints.geojson"

# The earthquake. Anything captured before this is pre-event imagery.
EVENT_DATE = date(2026, 6, 24)

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


def _fields() -> QgsFields:
    fields = QgsFields()
    fields.append(QgsField("layer_name", QVariant.String))
    fields.append(QgsField("label", QVariant.String))
    fields.append(QgsField("datetime", QVariant.Date))
    fields.append(QgsField("sensor", QVariant.String))
    fields.append(QgsField("gsd", QVariant.Double))
    fields.append(QgsField("location", QVariant.String))
    fields.append(QgsField("era", QVariant.String))
    return fields


def build() -> int:
    project = QgsProject.instance()
    scenes = dated_rasters(project)
    if not scenes:
        print("No dated rasters found - nothing to do.")
        return 1

    # Drop the existing footprints layer first: QGIS holds vector files open and
    # would flush its cached copy back over what we write.
    stale = [lyr.id() for lyr in project.mapLayers().values()
             if Path(lyr.source().split("|")[0]).name == OUT.name]
    for layer_id in stale:
        project.removeMapLayer(layer_id)
    if stale:
        print(f"removed {len(stale)} loaded copy/copies of {OUT.name} before writing")

    fields = _fields()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GeoJSON"
    options.fileEncoding = "UTF-8"
    writer = QgsVectorFileWriter.create(
        str(OUT), fields, QgsWkbTypes.Polygon, WGS84,
        project.transformContext(), options,
    )
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print("ERROR creating writer:", writer.errorMessage())
        return 1

    written = 0
    for layer, captured in scenes:
        extent = layer.extent()
        if extent.isEmpty():
            print(f"  skip (empty extent): {layer.name()}")
            continue

        geometry = QgsGeometry.fromRect(extent)
        # Rasters carry their own CRS (many are UTM); the index is WGS84.
        if layer.crs() != WGS84:
            transform = QgsCoordinateTransform(layer.crs(), WGS84, project)
            geometry.transform(transform)

        name = layer.name()
        sensor = sensor_of(name)
        gsd = gsd_of(name)
        location = location_of(name)
        bits = [b for b in (location, f"{sensor} {gsd:.2f}m" if gsd else sensor,
                            captured.isoformat()) if b]

        feature = QgsFeature(fields)
        feature.setGeometry(geometry)
        feature["layer_name"] = name
        feature["label"] = " · ".join(bits)
        feature["datetime"] = QDate(captured.year, captured.month, captured.day)
        feature["sensor"] = sensor
        feature["gsd"] = gsd
        feature["location"] = location
        feature["era"] = "before" if captured < EVENT_DATE else "after"
        writer.addFeature(feature)
        written += 1

    del writer  # flush and close

    print(f"wrote {written} footprints -> {OUT.relative_to(ROOT)}")

    fresh = QgsVectorLayer(str(OUT), "Imagery footprints (toggle)", "ogr")
    if fresh.isValid():
        # addMapLayer(..., False) then insert at the root: added normally it lands
        # in whatever group happens to be active, which is rarely what you want.
        project.addMapLayer(fresh, False)
        project.layerTreeRoot().insertLayer(0, fresh)
        print("re-added 'Imagery footprints (toggle)' at the top of the layer tree")
    else:
        print("WARNING: wrote the file but could not re-load it; add it manually.")
    return 0


# No __main__ guard: the QGIS console's Run button does not set __name__ to
# "__main__", so a guarded call would silently do nothing.
build()
