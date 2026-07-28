"""Custom QGIS expression functions for map decorations.

Paste the body of this file into the QGIS Expression dialog's **Function Editor**
tab (Expression dialog -> Function Editor -> New file), then press *Load*. The
functions register into the expression engine and become available anywhere
expressions are evaluated, including the Copyright Label decoration.

They live in the QGIS user profile (not the .qgz), so loading them produces no
diff in the repo. A collaborator who opens the project without loading this file
will see the decoration render an error string instead of the metadata.

Provides:
    imagery_date()    -> 'YYYY-MM-DD' acquisition date of the top imagery layer
    imagery_source()  -> attribution/licence string of that same layer
    imagery_label()   -> both, pre-joined for a decoration label

"Top imagery layer" means the topmost visible raster that (a) is checked on in
the layer tree, (b) is within its scale range, (c) actually overlaps the current
canvas view, and (d) is not a background basemap/hillshade.
"""

from qgis.core import (
    QgsCoordinateTransform,
    QgsProject,
    QgsRasterLayer,
)
from qgis.utils import qgsfunction

# Layers that are scenery rather than the imagery under inspection. These are
# global-coverage services that sit above the scene layers in the tree, so
# without excluding them they would shadow every scene. Matched
# case-insensitively as substrings against the layer name.
_BACKGROUND = (
    "hillshade",
    "openstreetmap",
    "world imagery",
    "wayback",
    "topo —",
)


def _overlaps_view(layer, map_settings):
    """True if the layer's footprint intersects the current canvas extent."""
    try:
        transform = QgsCoordinateTransform(
            layer.crs(), map_settings.destinationCrs(), QgsProject.instance()
        )
        extent = transform.transformBoundingBox(layer.extent())
    except Exception:
        # An un-transformable extent is not a reason to hide the layer.
        return True
    return extent.intersects(map_settings.visibleExtent())


def _top_imagery_layer(context):
    """The topmost visible raster overlapping the view, or None.

    QGIS already drops non-overlapping layers from the render list, but that is
    incidental behaviour; the explicit overlap test keeps an off-screen scene
    from ever supplying a date for ground it does not cover.
    """
    variables = context.variable("map_layers") if context else None
    if not variables:
        return None

    map_settings = None
    if context:
        # mapSettings is not exposed to expressions, so reach the canvas directly.
        from qgis.utils import iface

        if iface is not None:
            map_settings = iface.mapCanvas().mapSettings()

    for layer in variables:
        if not isinstance(layer, QgsRasterLayer):
            continue
        name = layer.name().lower()
        if any(token in name for token in _BACKGROUND):
            continue
        if map_settings is not None and not _overlaps_view(layer, map_settings):
            continue
        return layer
    return None


def _date_of(layer):
    """Acquisition date string for a layer, or '' when it carries none.

    Reads only the layer's temporal properties, set by scripts/set_temporal.py
    on dated scenes.

    DO NOT add a fallback through layer.metadata().extent().temporalExtents().
    Chaining off metadata() returns a temporary QgsLayerMetadata that is freed
    before the QList copy completes, and QGIS 3.44 segfaults in
    QgsLayerMetadata::Extent::temporalExtents(). Because this function runs from
    a canvas decoration on a repaint timer, that crash fires repeatedly and
    cannot be caught by try/except -- it is a hard SIGSEGV, not a Python
    exception. Always-on service layers (Wayback) therefore report no date.
    """
    if layer is None:
        return ""
    try:
        temporal = layer.temporalProperties()
        if temporal.isActive():
            begin = temporal.fixedTemporalRange().begin()
            if begin.isValid():
                return begin.toString("yyyy-MM-dd")
    except Exception:
        pass
    return ""


def _source_of(layer):
    """Attribution/licence string for a layer, or '' when it carries none."""
    if layer is None:
        return ""
    try:
        rights = layer.metadata().rights()
        return "; ".join(rights) if rights else ""
    except Exception:
        return ""


# NOTE ON SIGNATURES: with args=0 the decorator still passes the positional
# `values` list first, so every function must accept it before `feature`.
# Omitting it makes QGIS bind `values` to `feature` and then raise
# "got multiple values for argument 'feature'".


@qgsfunction(args=0, group="GEER", referenced_columns=[])
def imagery_date(values, feature, parent, context):
    """Acquisition date (YYYY-MM-DD) of the top imagery layer, from its
    temporal properties. Empty string when unavailable.

    <h4>Syntax</h4>
    <div class="syntax"><code>imagery_date()</code></div>
    """
    return _date_of(_top_imagery_layer(context))


@qgsfunction(args=0, group="GEER", referenced_columns=[])
def imagery_source(values, feature, parent, context):
    """Attribution/licence of the top imagery layer, from its metadata.
    Empty string when the layer carries no attribution.

    <h4>Syntax</h4>
    <div class="syntax"><code>imagery_source()</code></div>
    """
    return _source_of(_top_imagery_layer(context))


@qgsfunction(args=0, group="GEER", referenced_columns=[])
def imagery_label(values, feature, parent, context):
    """Date and source of the top imagery layer joined for a decoration label,
    e.g. '2026-06-27  ·  CC BY-NC 4.0, © Planet Labs PBC'. Omits whichever
    part is missing, and returns '' when neither is available.

    <h4>Syntax</h4>
    <div class="syntax"><code>imagery_label()</code></div>
    """
    layer = _top_imagery_layer(context)
    parts = (_date_of(layer), _source_of(layer))
    return "  ·  ".join(part for part in parts if part)
