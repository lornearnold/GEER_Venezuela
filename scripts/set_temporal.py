"""Give every dated raster a temporal range, so the Temporal Controller can filter it.

Run inside QGIS: Plugins > Python Console > Show Editor > open this > Run.
Then open View > Panels > Temporal Controller and drag the slider.

Each scene gets a one-day window [capture 00:00, next day 00:00). With the
controller in Animation mode stepping 1 day, imagery appears and disappears by
capture date; in Fixed Range mode it acts as a date filter. Either way the map
itself tells you the date of what you're seeing.

Idempotent - re-run any time layers are added or re-loaded. To undo, set
ENABLE = False at the bottom of this file and run it again.

Layers that are NOT dated scenes (NASA services, Wayback, hillshade, OSM) are
left alone deliberately, so they stay visible at every point on the timeline
rather than blinking out. See scripts/imagery_index.py to change that rule.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

from qgis.core import QgsDateTimeRange, QgsProject, QgsRasterLayerTemporalProperties
from qgis.PyQt.QtCore import QDate, QDateTime, QTime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imagery_index import dated_rasters, is_service_layer  # noqa: E402


def _qdatetime(d) -> QDateTime:
    return QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0, 0))


def apply_temporal(enable: bool = True) -> int:
    project = QgsProject.instance()
    scenes = dated_rasters(project)
    if not scenes:
        print("No dated rasters found - nothing to do.")
        return 1

    for layer, captured in scenes:
        props = layer.temporalProperties()
        if not enable:
            props.setIsActive(False)
            continue
        begin = _qdatetime(captured)
        end = _qdatetime(captured + timedelta(days=1))
        props.setMode(QgsRasterLayerTemporalProperties.ModeFixedTemporalRange)
        props.setFixedTemporalRange(QgsDateTimeRange(begin, end))
        props.setIsActive(True)
        layer.triggerRepaint()

    if enable:
        first, last = scenes[0][1], scenes[-1][1]
        print(f"temporal range set on {len(scenes)} scenes: {first} .. {last}")
        print("open View > Panels > Temporal Controller, set step = 1 day, and scrub.")
    else:
        print(f"temporal properties cleared on {len(scenes)} scenes")

    skipped = [lyr.name() for lyr in project.mapLayers().values()
               if lyr.__class__.__name__ == "QgsRasterLayer" and is_service_layer(lyr.name())]
    print(f"left alone (always-on service/basemap layers): {len(skipped)}")
    return 0


# Set to False and re-run to strip temporal properties and go back to plain toggling.
# (A --off command-line flag is useless here: run from the QGIS console, sys.argv
# belongs to QGIS itself, not to this script.)
ENABLE = True

# No __main__ guard: the QGIS console's Run button does not set __name__ to
# "__main__", so a guarded call would silently do nothing.
apply_temporal(enable=ENABLE)
