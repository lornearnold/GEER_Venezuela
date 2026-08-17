"""Gradient-fill the watershed polygons by landslide density, computed live.

Run inside QGIS: Plugins > Python Console > Show Editor > open this > Run.

Two metrics, both normalised by watershed area, switched by the project variable
`ls_metric`:

    count   landslides per km^2      (how MANY failures per unit area)
    area    landslide area as % of watershed   (how MUCH of it failed)

Only polygons with Type = 'Landslide' in the geomorph aerials layer are counted;
Liquefaction / Ground Rupture / Ground Settlement are excluded.

Switching metric
----------------
Set METRIC below and re-run, or change it live without touching this file:

    Project > Properties > Variables > ls_metric   ->  count | area

then right-click the layer > Symbology > Classify to recompute the breaks.

Checking a number
-----------------
`rank("area")` (called at the bottom) prints every watershed ranked by landslide
area-percent, worst first, plus the max and the area-weighted mean. It evaluates
the same expression the renderer uses, so it is the way to confirm a figure
quoted in the report actually came from the inventory rather than from a
symbology break. `rank("count")` does the same for landslides / km².

Why expressions and not a new field
-----------------------------------
The values are computed at render time with overlay_intersects(), so nothing is
written into either source layer -- the watershed shapefile and the aerials keep
their original attributes. Change the aerials (add a polygon, fix a Type) and
the map updates on the next repaint with no re-run of any join.

Cost is ~1 s for all 41 watersheds against 452 landslide polygons, which is fine
for a layer this size but is recomputed on every repaint; if the inventory grows
by an order of magnitude, materialise it instead.
"""

from __future__ import annotations

from qgis.core import (
    QgsClassificationQuantile,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFillSymbol,
    QgsGradientColorRamp,
    QgsGraduatedSymbolRenderer,
    QgsProject,
    QgsRendererRangeLabelFormat,
)
from qgis.PyQt.QtGui import QColor

WATERSHEDS = "Watershed landslide coverage (GeoSyntec, 2026-07-25)"
AERIALS = "GeoSyntec geomorph aerials (2026-07-20)"

# 'count' -> landslides per km^2; 'area' -> landslide area as % of watershed.
METRIC = "count"

N_CLASSES = 5
RAMP_LOW = QColor(255, 245, 235)
RAMP_HIGH = QColor(140, 20, 15)


def _layer(name: str):
    matches = [l for l in QgsProject.instance().mapLayers().values() if l.name() == name]
    if not matches:
        raise SystemExit(f"layer not found: {name!r}")
    return matches[0]


def _expressions(aerials_id: str) -> tuple[str, str, str]:
    """(count-per-km2, area-percent, switchable) expressions.

    NOTE: inside overlay_intersects(), $geometry is the *aerials* feature and
    QGIS has already reprojected it into the watershed layer's CRS. Do not wrap
    it in transform() -- doing so reprojects already-projected coordinates and
    silently yields inf, making every intersection area come out as zero.
    """
    count = (
        "array_length(\n"
        "  overlay_intersects(\n"
        f"    layer := '{aerials_id}',\n"
        "    expression := $id,\n"
        "    filter := \"Type\" = 'Landslide'\n"
        "  )\n"
        ') / "Area_sqkm"'
    )
    area = (
        "(\n"
        "  coalesce(\n"
        "    array_sum(\n"
        "      array_foreach(\n"
        "        overlay_intersects(\n"
        f"          layer := '{aerials_id}',\n"
        "          expression := $geometry,\n"
        "          filter := \"Type\" = 'Landslide'\n"
        "        ),\n"
        "        area(intersection(@element, $geometry))\n"
        "      )\n"
        "    ), 0) / 1000000.0\n"
        ') / "Area_sqkm" * 100'
    )
    switchable = (
        "CASE\n"
        f"  WHEN @ls_metric = 'area' THEN ({area})\n"
        f"  ELSE ({count})\n"
        "END"
    )
    return count, area, switchable


def style(metric: str = METRIC) -> int:
    project = QgsProject.instance()
    watersheds = _layer(WATERSHEDS)
    aerials = _layer(AERIALS)

    _, _, value_expr = _expressions(aerials.id())

    variables = dict(project.customVariables())
    variables["ls_metric"] = metric
    project.setCustomVariables(variables)

    symbol = QgsFillSymbol.createSimple({
        "color": "255,255,255,255",
        "outline_color": "60,60,60,255",
        "outline_width": "0.26",
    })
    ramp = QgsGradientColorRamp(RAMP_LOW, RAMP_HIGH)

    renderer = QgsGraduatedSymbolRenderer(value_expr)
    renderer.setSourceSymbol(symbol.clone())
    renderer.setSourceColorRamp(ramp)
    renderer.setClassificationMethod(QgsClassificationQuantile())
    renderer.updateClasses(watersheds, N_CLASSES)
    renderer.setLabelFormat(QgsRendererRangeLabelFormat("%1 - %2", 2), True)
    renderer.updateColorRamp(ramp)

    watersheds.setRenderer(renderer)
    watersheds.setOpacity(0.75)
    watersheds.triggerRepaint()

    units = "landslides / km²" if metric == "count" else "% of watershed area"
    print(f"styled {watersheds.name()!r} by {metric} ({units})")
    for rng in renderer.ranges():
        print(f"    {rng.lowerValue():9.3f} - {rng.upperValue():9.3f}")
    print("\nswitch metric: Project > Properties > Variables > ls_metric = count | area")
    print("then Symbology > Classify to recompute the breaks.")
    return 0


def rank(metric: str = "area", top: int = 0) -> list[tuple[str, float]]:
    """Print watersheds ranked by `metric`, worst first, and return the ranking.

    Evaluates the *same* expression the renderer uses, so the printed numbers are
    by construction the ones on the map -- this is the check that a quoted figure
    ("the worst watershed is 4-5%") actually came from the data. Reads only; like
    style(), it writes nothing into either source layer.

    `top` limits the printed rows (0 = all); the full list is always returned.
    """
    count_expr, area_expr, _ = _expressions(_layer(AERIALS).id())
    watersheds = _layer(WATERSHEDS)

    expression = QgsExpression(area_expr if metric == "area" else count_expr)
    context = QgsExpressionContext()
    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(watersheds))
    expression.prepare(context)

    # Name field varies between GeoSyntec deliveries; fall back to the fid.
    fields = [f.name() for f in watersheds.fields()]
    name_field = next(
        (f for f in ("Name", "NAME", "Watershed", "NOMBRE", "Nombre") if f in fields),
        None,
    )

    ranking = []
    for feature in watersheds.getFeatures():
        context.setFeature(feature)
        value = expression.evaluate(context)
        if expression.hasEvalError():
            raise SystemExit(f"expression error: {expression.evalErrorString()}")
        label = str(feature[name_field]) if name_field else f"fid {feature.id()}"
        ranking.append((label, float(value or 0.0), float(feature["Area_sqkm"])))

    ranking.sort(key=lambda row: row[1], reverse=True)

    units = "landslides / km²" if metric == "count" else "% of watershed area"
    print(f"\n{watersheds.name()!r} ranked by {metric} ({units}) -- {len(ranking)} watersheds")
    print(f"    {'watershed':<34} {'value':>9}  {'km²':>8}")
    for label, value, area_sqkm in ranking[: top or len(ranking)]:
        print(f"    {label:<34} {value:9.3f}  {area_sqkm:8.2f}")

    nonzero = [r for r in ranking if r[1] > 0]
    print(
        f"\n    max {ranking[0][1]:.3f} ({ranking[0][0]}); "
        f"{len(nonzero)}/{len(ranking)} watersheds > 0"
    )
    if nonzero:
        total = sum(r[1] * r[2] for r in ranking) / sum(r[2] for r in ranking)
        print(f"    area-weighted mean across all watersheds: {total:.3f}")
    print(
        "    NB: GeoSyntec aerial polygons with Type = 'Landslide' only -- a lower\n"
        "    bound on true areal coverage wherever mapping is incomplete."
    )
    return [(label, value) for label, value, _ in ranking]


# No __main__ guard: the QGIS console's Run button does not set __name__ to
# "__main__", so a guarded call would silently do nothing.
style()

# Verify a quoted areal-percent figure against the data. Comment out if you only
# want the restyle.
rank("area")
