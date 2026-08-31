"""One-button spatial filter for the AFTER imagery layers.

Loaded by the project's openProject() macro (or manually:
    import sys; sys.path.insert(0, QgsProject.instance().homePath())
    import after_filter; after_filter.install()
).

"Filter AFTER to view" marks every AFTER imagery layer whose footprint does not
intersect the current canvas extent as Private (hidden from the Layers panel,
unchecked). "Show all AFTER" clears the flags. install() always clears stale
flags first, so a project saved while filtered reopens clean.
"""
import os

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsMapLayer,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QKeySequence
from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface

AFTER_GROUPS = (
    "AFTER — post-event imagery (stream)",
    "AFTER — post-event imagery (external drive)",
)
FOOTPRINTS = os.path.join("..", "data", "imagery", "imagery_footprints.geojson")
TOOLBAR_NAME = "afterFilterToolbar"
WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")

_toolbar = None
_actions = []
_footprints = None  # layer_name -> QgsGeometry (EPSG:4326)


def _project():
    return QgsProject.instance()


def footprints():
    """Footprint polygons keyed by layer name, loaded once per install()."""
    global _footprints
    if _footprints is None:
        _footprints = {}
        loaded = _project().mapLayersByName("Imagery footprints")
        if loaded:
            lyr = loaded[0]  # project copy first: sees uncommitted edits
        else:
            path = os.path.normpath(os.path.join(_project().homePath(), FOOTPRINTS))
            lyr = QgsVectorLayer(path, "footprints", "ogr")
        if lyr.isValid():
            xf = QgsCoordinateTransform(lyr.crs(), WGS84, _project())
            for f in lyr.getFeatures():
                g = QgsGeometry(f.geometry())
                if lyr.crs() != WGS84:
                    g.transform(xf)
                _footprints[f["layer_name"]] = g
    return _footprints


def after_layers():
    root = _project().layerTreeRoot()
    seen, out = set(), []
    for gname in AFTER_GROUPS:
        grp = root.findGroup(gname)
        if grp is None:
            continue
        for node in grp.findLayers():
            lyr = node.layer()
            if lyr is not None and lyr.id() not in seen:
                seen.add(lyr.id())
                out.append(lyr)
    return out


def _layer_geom(lyr):
    g = footprints().get(lyr.name())
    if g is not None:
        return g
    ext = lyr.extent()
    if lyr.crs().isValid() and lyr.crs() != WGS84:
        ext = QgsCoordinateTransform(lyr.crs(), WGS84, _project()).transformBoundingBox(ext)
    return QgsGeometry.fromRect(ext)


def _set_private(lyr, private):
    flags = lyr.flags()
    new = (flags | QgsMapLayer.Private) if private else (flags & ~QgsMapLayer.Private)
    if new != flags:
        lyr.setFlags(new)


def _uncheck(layer_id):
    for node in _project().layerTreeRoot().findLayers():
        if node.layerId() == layer_id:
            node.setItemVisibilityChecked(False)


def _refresh():
    view = iface.layerTreeView()
    if hasattr(view, "proxyModel"):
        view.proxyModel().invalidateFilter()


def filter_to_view():
    canvas = iface.mapCanvas()
    rect = canvas.extent()
    ccrs = canvas.mapSettings().destinationCrs()
    if ccrs != WGS84:
        rect = QgsCoordinateTransform(ccrs, WGS84, _project()).transformBoundingBox(rect)
    view = QgsGeometry.fromRect(rect)
    layers = after_layers()
    hits = 0
    for lyr in layers:
        if _layer_geom(lyr).intersects(view):
            hits += 1
            _set_private(lyr, False)
        else:
            _set_private(lyr, True)
            _uncheck(lyr.id())
    _refresh()
    iface.messageBar().pushInfo("AFTER filter", f"{hits}/{len(layers)} AFTER layers cover the view")
    return hits


def show_all():
    layers = after_layers()
    for lyr in layers:
        _set_private(lyr, False)
    _refresh()
    return len(layers)


def uninstall():
    global _toolbar, _actions
    for a in _actions:
        try:
            iface.unregisterMainWindowAction(a)
        except Exception:
            pass
    _actions = []
    for tb in iface.mainWindow().findChildren(type(iface.attributesToolBar()), TOOLBAR_NAME):
        iface.mainWindow().removeToolBar(tb)
        tb.setObjectName("")  # pending deleteLater must not match the next uninstall()
        tb.deleteLater()
    _toolbar = None


def install():
    global _toolbar, _actions, _footprints
    uninstall()
    _footprints = None
    show_all()  # clear any flags persisted in a saved-while-filtered project
    _toolbar = iface.addToolBar("AFTER filter")
    _toolbar.setObjectName(TOOLBAR_NAME)
    a_filter = QAction("Filter AFTER to view", iface.mainWindow())
    a_filter.setToolTip("Hide AFTER imagery layers whose footprint misses the current view (Ctrl+Shift+F)")
    a_filter.triggered.connect(lambda *_: filter_to_view())
    a_all = QAction("Show all AFTER", iface.mainWindow())
    a_all.setToolTip("Un-hide all AFTER imagery layers")
    a_all.triggered.connect(lambda *_: (show_all(), iface.messageBar().pushInfo("AFTER filter", "all AFTER layers shown")))
    _toolbar.addAction(a_filter)
    _toolbar.addAction(a_all)
    iface.registerMainWindowAction(a_filter, QKeySequence("Ctrl+Shift+F").toString())
    _actions = [a_filter, a_all]
    return _toolbar
