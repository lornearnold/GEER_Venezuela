---
name: geer-report
description: >
  Build or update the GEER Venezuela field report, a supplement, and the candidate
  KMZ from the QGIS candidate sites. Use when asked to generate/refresh the report or
  a supplement, render figures for newly added sites, add sites to a group's page, or
  update the KMZ. Handles the whole QGIS→PDF/KMZ pipeline: deterministic Python steps
  plus the QGIS-mcp figure rendering.
---

# /geer-report — the one command for reports, supplements, and the KMZ

The candidate sites in QGIS are the single source of truth. There is **no plan file**:
sections, groups, order, and the table all derive from site attributes. The only choices
per build are **mode** (full report with cover, or supplement with a badge) and a **site
selection** (all / a list / a range). Reports must be deterministic — figures are rendered
with explicit layers and extents, never from the current QGIS view or active layers.

## Inputs

- **mode**: `full` (cover page, no badge) or `supplement` (no cover, `Supplement N` badge).
- **selection**: `all`, a list (`3,4,94`), a range (`111-123`), or a mix. A group is pulled
  in whole if any member is selected.
- **label** (supplements): e.g. `Supplement 1` (defaults to `Supplement 1`).

## Pipeline (run in order)

Work in the repo root; scripts live in `reports/`. QGIS must be open with the project
loaded and qgis-mcp **Start Server** clicked (`mcp__qgis__ping` to confirm) — but only for
the figure-rendering step. The Python steps read files off disk and don't touch QGIS.

### 1. Refresh attributes (only if sites were added/edited since last build)

```
uv run python reports/compute_road_dist.py     # nearest-drivable-road distance → geojson
uv run python reports/export_site_data.py       # geojson attributes → reports/site_data.json
```

`compute_road_dist.py` writes `road_dist_m` back into the candidate GeoJSON. **CLAUDE.md
gotcha:** QGIS caches an open layer and will clobber the write. Either (a) run it via mcp
inside QGIS's own edit session instead, or (b) remove the "Candidate sites" layer in QGIS
→ run the script → re-add a fresh layer. Preview first with `--dry-run` / `--only 111-123`.

### 2. Find which units still need figures

```
uv run python reports/build_report.py --mode <mode> --sites <selection> --no-compile
```

This is the **"only process new/changed sites" check.** It compares the classified units
against `figures/manifest.json` and **exits non-zero listing units that need a (re)render**:
- `no figure yet` — a new ungrouped site or a brand-new group (never rendered).
- `membership changed [old] -> [new]` — an existing group whose figure predates a site being
  added to (or removed from) it.

That list is your render worklist for step 3 — already-processed, unchanged units are skipped.
If it succeeds with no list, everything is current; skip to step 4. (`--sites` scopes the
worklist to what you're building.)

### 3. Render the missing/requested figures (QGIS-mcp) and update the manifest

For **each** unit on the worklist, render a **main figure** and a **locator**, save PNGs to
`reports/figures/`, and add/update its entry in `reports/figures/manifest.json`. Use the
**Rendering playbook** below. Re-rendering an existing unit (e.g. after a site was added to a
group, or `--sites` names it explicitly) just overwrites its figures + manifest entry.

To render a *group* page, the sites must share a `group` attribute in QGIS. Ungrouped sites
render as one page each. If the user wants several ungrouped sites on a single page, set their
`group` attribute in QGIS first (or ask them to) — do **not** cluster them by spatial judgment;
that reintroduces non-deterministic grouping.

### 4. Build the PDF

```
uv run python reports/build_report.py --mode full --out reports/report.pdf
uv run python reports/build_report.py --mode supplement --label "Supplement 1" --sites 111-123 --out reports/supplement_1.pdf
```

### 5. Refresh the KMZ (covers all sites regardless of the report selection)

```
uv run python reports/export_kmz.py
```

### 6. Report back

State the output paths, page counts, which units were newly rendered, and flag any imagery-
limited figures (cloud/haze/deep shadow) so the user knows what to eyeball.

---

## Rendering playbook (step 3 detail)

All rendering is PyQGIS through `mcp__qgis__execute_code`. **Determinism rules:** always
`QgsMapSettings.setLayers([...])` with explicit layer objects (never `iface`/canvas/active
layers); set the extent and output size explicitly; a socket timeout at ~60 s doesn't stop
QGIS — poll the output file. Resolve layers by **name** (names are stable; layer IDs are not).

### Geometry, scale, exact-scale trick

Render in **EPSG:32619** at **300 dpi**. To lock an exact 1:N scale, fix the pixel size and
derive the extent: `half_extent_m = scale * (px / dpi) * 0.0254 / 2`, centered on the unit.

**Scale ladder** (increase a step if the sites don't fit the figure):

| unit spread | scale | bar_m | main px (w×h) |
|---|---|---|---|
| single site | 1:2000 (1:3000 if imagery is coarse ≥0.7 m) | 50 (100) | 2000×1500 |
| small group (≲700 m) | 1:6000 | 200 | 2000×1600 |
| group ≲1.2 km | 1:8000–10000 | 250 | 2000×1500 |
| group ≲2.5 km | 1:20000 | 500 | 2000×1500 |
| §6 bundle (whole AOI) | 1:150000 | 5000 | wide |

Keep the main figure landscape-ish (height ≤ ~1600 px) so figure **+** the site table fit on
one page. Center on the units' bbox; pad so labels don't clip and **no site hides under the
top-right locator inset** (nudge the center if one does — that happened with site 115).

### Main figure

Layers top→bottom: `[Candidate sites (labeled), <imagery scene>, <underlay scene if needed>]`,
background `#1a1a1a` (nodata reads as dark, not white). Labels ON (`DrawLabeling`), antialias ON.

**Imagery pick** (this is the judgment part — record what you chose):
- Prefer the **lowest-GSD post-event scene whose footprint contains the whole figure extent**.
  Sample the scene's RGB at the sites (`provider.sample`, transform point to the raster CRS) to
  catch cloud/shadow/nodata before committing.
- Avoid **cloud** (bright grey, high value) and **nodata** (NaN → white gap). If the primary
  scene has a nodata corner, **underlay** a second covering scene beneath it.
- For **deep-shadow** slopes (RGB ~20–50, near-black), brighten with a contrast stretch on a
  **cloned** renderer (don't touch the project layer): `QgsContrastEnhancement` /
  `StretchToMinimumMaximum`, min 0, max ~110 (bright scenes: ~150). 112/113 shadow recovered at 0–110.
- **Vantor mosaic is last-resort** (cloudy / nighttime-looking) — only when nothing else covers.

### Locator inset

Layers `[red-box, Candidate sites (dots), Google roadmap]`, **no labels**, white background,
scale = **map_scale × 50**, ~900×900 px. Base = Google Maps roadmap XYZ (matches the main
report). Candidate dots at **1.3 mm** (half the map symbol, so they don't swamp the box). Red
box = the main figure's exact extent.

### Reference render code (adapt per unit)

```python
from qgis.core import (QgsProject, QgsRasterLayer, QgsMapSettings, QgsMapRendererParallelJob,
                       QgsCoordinateReferenceSystem, QgsRectangle, QgsContrastEnhancement,
                       QgsVectorLayer, QgsFeature, QgsGeometry, QgsFillSymbol)
from qgis.PyQt.QtCore import QSize, QEventLoop
from qgis.PyQt.QtGui import QColor
P = QgsProject.instance(); UTM = QgsCoordinateReferenceSystem('EPSG:32619')
def layer(sub):  # resolve by name substring
    return next(l for l in P.mapLayers().values() if sub in l.name())
def stretched(lyr, vmax=110, vmin=0):
    l = lyr.clone(); r = l.renderer().clone()
    for s in ('setRedContrastEnhancement','setGreenContrastEnhancement','setBlueContrastEnhancement'):
        ce = QgsContrastEnhancement(); ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
        ce.setMinimumValue(vmin); ce.setMaximumValue(vmax); getattr(r, s)(ce)
    l.setRenderer(r); return l
def small_dots(lyr, size=1.3):
    l = lyr.clone(); r = l.renderer().clone(); r.symbol().setSize(size); l.setRenderer(r); return l
def box(ext):
    vl = QgsVectorLayer('Polygon?crs=EPSG:32619','b','memory'); f = QgsFeature()
    f.setGeometry(QgsGeometry.fromRect(QgsRectangle(*ext))); vl.dataProvider().addFeature(f)
    vl.renderer().setSymbol(QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'227,26,28','outline_width':'0.5'})); return vl
def google():
    return QgsRasterLayer('type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D{x}%26y%3D{y}%26z%3D{z}&zmax=20&zmin=0','g','wms')
def render(layers, cx, cy, scale, out, w=2000, h=1500, dpi=300, bg='#1a1a1a', labels=True):
    ms = QgsMapSettings(); ms.setDestinationCrs(UTM); ms.setLayers(layers)
    ms.setOutputSize(QSize(w,h)); ms.setOutputDpi(dpi); ms.setBackgroundColor(QColor(bg))
    ms.setFlag(QgsMapSettings.DrawLabeling, labels); ms.setFlag(QgsMapSettings.Antialiasing, True)
    hw = scale*(w/dpi)*0.0254/2; hh = scale*(h/dpi)*0.0254/2
    ext = QgsRectangle(cx-hw, cy-hh, cx+hw, cy+hh); ms.setExtent(ext)
    j = QgsMapRendererParallelJob(ms); loop = QEventLoop(); j.finished.connect(loop.quit)
    j.start(); loop.exec_(); j.renderedImage().save(out); return [ext.xMinimum(),ext.yMinimum(),ext.xMaximum(),ext.yMaximum()]
```

Always eyeball each PNG (Read the file) before accepting it — check for cloud, nodata gaps,
sites hidden by the inset, and label clipping.

### Manifest entry to write per unit

`reports/figures/manifest.json` → `units[<key>]` where `<key>` is the group name, the site
number as a string, or `"bundle"` (must match `_classify.build_units`):

```json
{ "kind": "group|site|bundle", "site_nos": [ ... ], "scale": 6000, "bar_m": 200,
  "locator_scale": 300000, "fig": "figures/xxx_main.png", "locator": "figures/xxx_loc.png",
  "credit": "Post-event imagery: Planet SkySat, 0.73 m GSD, 2026-06-27, contrast-enhanced © 2026 Planet Labs PBC.",
  "scenes": [{"scene_id": "...", "sensor": "...", "gsd": 0.73, "date": "2026-06-27"}],
  "ext_utm": [xmin, ymin, xmax, ymax] }
```

When the set of scenes used across the packet changes, refresh `manifest.cover.source_rows`
(the "Imagery reviewed" table on the cover) too.

## Files this skill drives

| File | Role | Automated? |
|---|---|---|
| `reports/compute_road_dist.py` | nearest-road distance → geojson | ✅ python |
| `reports/export_site_data.py` | geojson → `site_data.json` | ✅ python |
| `reports/_classify.py` | sections/groups/order from attributes (shared) | ✅ python |
| `reports/build_report.py` | classify + join manifest → `build/pages.json` → PDF | ✅ python |
| `reports/report.typ` / `template.typ` | thin renderer / machinery | ✅ typst |
| `reports/export_kmz.py` | attribute-classified KMZ | ✅ python |
| `reports/figures/manifest.json` | per-unit render metadata + cover | ⚠️ **this skill** (QGIS-mcp) |
| `reports/figures/*.png` | main figures + locators + cover map | ⚠️ **this skill** (QGIS-mcp) |

Only the last two rows need QGIS-mcp; everything else is a plain `uv run`.
