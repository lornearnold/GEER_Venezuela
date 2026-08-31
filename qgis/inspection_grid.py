"""Review-progress plumbing for the inspection grid.

- Registers the expression function grid_progress(parent_id, kind) — kind in
  ('reviewed', 'unreviewable', 'total') — backed by a one-pass cache over the
  1 km grid, invalidated whenever that layer changes. The 10 km layer's
  virtual fields (n_reviewed, n_unreviewable, pct_done) use it, so it
  styles/labels as a live progress map without per-feature scans.
- Stamps status_change_date at commit time for every 1 km feature whose
  status actually changed ("apply default on update" only covers form edits).
  A backfill from NULL to 'unreviewed' does not bump the date.

Loaded by the project's openProject() macro alongside after_filter.
"""
from qgis.core import (
    QgsExpression,
    QgsFeatureRequest,
    QgsField,
    QgsProject,
    qgsfunction,
)
from qgis.PyQt.QtCore import QDate, QVariant

G1_NAME = "Inspection grid 1 km"
G10_NAME = "Inspection grid 10 km"
VIRTUAL_FIELDS = {
    "n_reviewed": ("grid_progress(\"cell_id\", 'reviewed')", QVariant.Int),
    "n_unreviewable": ("grid_progress(\"cell_id\", 'unreviewable')", QVariant.Int),
    "pct_done": (
        "round(100.0 * (grid_progress(\"cell_id\", 'reviewed')"
        " + grid_progress(\"cell_id\", 'unreviewable'))"
        " / nullif(grid_progress(\"cell_id\", 'total'), 0), 1)",
        QVariant.Double,
    ),
}

_cache = None  # parent_id -> {'total': n, 'reviewed': n, 'unreviewable': n}
_connections = []  # (signal, slot) pairs for uninstall()


def _layer(name):
    layers = QgsProject.instance().mapLayersByName(name)
    return layers[0] if layers else None


def invalidate(*_):
    global _cache
    _cache = None


def _counts():
    global _cache
    if _cache is None:
        counts = {}
        lyr = _layer(G1_NAME)
        if lyr is None:
            return {}
        for f in lyr.getFeatures():
            c = counts.setdefault(f["parent_id"], {"total": 0, "reviewed": 0, "unreviewable": 0})
            c["total"] += 1
            s = f["status"]
            if s in ("reviewed", "unreviewable"):
                c[s] += 1
        _cache = counts
    return _cache


@qgsfunction(args="auto", group="GEER", usesGeometry=False)
def grid_progress(parent_id, kind, feature, parent):
    """Count of 1 km cells with the given status under a 10 km cell.

    grid_progress('19PDM60', 'reviewed') -> int; kind: reviewed | unreviewable | total
    """
    return _counts().get(parent_id, {}).get(kind, 0)


def stamp_dates(layer):
    """Set status_change_date on buffered features whose status differs from disk."""
    buffer = layer.editBuffer()
    if buffer is None:
        return 0
    i_status = layer.fields().indexOf("status")
    i_date = layer.fields().indexOf("status_change_date")
    changed = buffer.changedAttributeValues()
    fids = [fid for fid, attrs in changed.items() if i_status in attrs]
    if not fids:
        return 0
    request = (
        QgsFeatureRequest()
        .setFilterFids(fids)
        .setSubsetOfAttributes([i_status])
        .setFlags(QgsFeatureRequest.NoGeometry)
    )
    old = {f.id(): f["status"] for f in layer.dataProvider().getFeatures(request)}
    today = QDate.currentDate()
    n = 0
    for fid in fids:
        new = changed[fid][i_status]
        prev = old.get(fid)
        prev = prev if isinstance(prev, str) else None
        new_s = new if isinstance(new, str) else None
        if new_s == prev:
            continue
        if prev is None and new_s == "unreviewed":  # backfill, not a real change
            continue
        if i_date in changed[fid]:  # explicit date edit wins
            continue
        layer.changeAttributeValue(fid, i_date, today)
        n += 1
    return n


def install():
    uninstall()
    QgsExpression.registerFunction(grid_progress)
    g1 = _layer(G1_NAME)
    if g1 is not None:
        for sig in (g1.attributeValueChanged, g1.committedAttributeValuesChanges,
                    g1.editingStopped, g1.dataChanged):
            sig.connect(invalidate)
            _connections.append((sig, invalidate))
        stamper = lambda *_: stamp_dates(g1)
        g1.beforeCommitChanges.connect(stamper)
        _connections.append((g1.beforeCommitChanges, stamper))
    g10 = _layer(G10_NAME)
    if g10 is not None:
        for name, (expr, qtype) in VIRTUAL_FIELDS.items():
            idx = g10.fields().indexOf(name)
            if idx >= 0:
                g10.removeExpressionField(idx)
            g10.addExpressionField(expr, QgsField(name, qtype))
        g10.triggerRepaint()
    invalidate()


def uninstall():
    global _connections
    QgsExpression.unregisterFunction("grid_progress")
    for sig, slot in _connections:
        try:
            sig.disconnect(slot)
        except Exception:
            pass
    _connections = []
