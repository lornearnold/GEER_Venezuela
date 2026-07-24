# scripts/ — date-aware imagery navigation

Three small scripts that make "what am I looking at, and what else covers this spot?"
answerable from the map instead of from the Layers panel.

They run **inside QGIS** (Plugins ► Python Console ► Show Editor ► open script ► Run),
because they need the live project. Nothing here mutates your imagery; the only things
written are one GeoJSON sidecar and each raster's temporal properties.

## Why these don't run in the repo's uv venv

**PyQGIS is not a pip package.** It ships as compiled libraries inside `QGIS.app`, built
against that exact Qt/GDAL/PROJ stack. `uv add qgis` cannot install it — the `qgis` project
on PyPI is unrelated, and there is no wheel for the real thing.

Worse, the venv appears to have it. `uv run python -c "import qgis"` **succeeds**, because
this repo contains a `qgis/` *directory* (holding `geer_venezuela.qgz`) and Python treats any
such directory as a namespace package. It has no `.core`:

    $ uv run python -c "import qgis; print(qgis.__path__)"
    ['/Users/…/GEER_Venezuela/qgis']          # <- the project folder, not PyQGIS
    $ uv run python -c "import qgis.core"
    ModuleNotFoundError: No module named 'qgis.core'

So the venv (Python 3.12.0) is for the `src/geer_venezuela/` data-fetching modules, which use
geopandas/rasterio/pystac and never import PyQGIS. Anything touching `qgis.*` runs under
QGIS's own interpreter (Python 3.12.11, `/Applications/QGIS.app/Contents/MacOS/QGIS`).
Two separate interpreters, by necessity.

### Running them

**In the GUI (recommended)** — Plugins ► Python Console ► Show Editor ► open ► Run. The
live project is already loaded, and streaming layers work.

> **If Run prints nothing, look for `if __name__ == "__main__":`.** The console's Run button
> executes a file *without* setting `__name__` to `"__main__"`, so that guard is False and
> the script loads without ever calling anything — no output, no error. The scripts here
> therefore call their entry point unguarded at the bottom. Keep it that way in anything you
> add, or run it with `exec(open(path).read())` from the console instead.

**Headless from VSCode/terminal** — `./scripts/run_headless.sh scripts/foo.py`. The wrapper
sets `PYTHONHOME`, `PROJ_DATA`, and `GDAL_DATA`, which the app bundle normally sets for
itself; without `PROJ_DATA` every CRS transform fails with "Cannot find proj.db". A headless
script must build its own `QgsApplication` and call `QgsProject.instance().read(...)`.

  Caveat: headless runs have no network/auth context, so streaming layers (NASA services,
  Esri basemaps) load **invalid with a Null extent**. The scripts here only touch local
  dated rasters, so they are unaffected — but do not trust a headless run to see everything
  the GUI sees.

### VSCode autocomplete

The editor cannot resolve `qgis.*` from the venv either. To get completions, add to
`.vscode/settings.json`:

    {
      "python.analysis.extraPaths": [
        "/Applications/QGIS.app/Contents/Frameworks/lib/python3.12/site-packages"
      ]
    }

That is the copy the running QGIS actually imports — the bundle also ships a stale
`Contents/Resources/python3.11/site-packages/qgis`, which is *not* the one in use. This is
type-hint sugar only; running still requires one of the two paths above.

| script | what it does | when to run |
|---|---|---|
| `inspect_project.py` | prints the real layer registry and flags anything that makes a name lookup ambiguous | when a script's output looks wrong |
| `build_footprints.py` | writes one polygon per dated raster into `data/basemaps/imagery_footprints.geojson`, carrying date/sensor/gsd/location | after adding or removing imagery |
| `set_temporal.py` | sets each dated raster's temporal range from its capture date, so the Temporal Controller can filter them | after `build_footprints.py`, or any time layers were re-added |
| `whats_here.py` | prints every image covering the current canvas centre, sorted by date | ad hoc, while zoomed in |

## How do I know a script is reading the right layers?

Not from the Layers panel — it is a *view* of the project, not the project. QGIS keeps two
structures: the **registry** (every loaded layer: source, symbology, fields) and the **layer
tree** (grouping, order, checkboxes). A layer can exist in one and not the other, and two
panel rows can share a name.

That matters because a script that looks a layer up by name can silently pick the wrong one.
Three defences, in order of strength:

1. **Read the file, not the project.** `whats_here.py` opens
   `imagery_footprints.geojson` directly, so no registry ambiguity is possible.
2. **Match on source path, not name.** `build_footprints.py` finds stale copies by file
   path and removes *all* of them — paths are unique, display names are not.
3. **Warn when a name is ambiguous.** `whats_here.py` must match by name to read checkbox
   state, so it prints a warning if any name is duplicated.

When output looks wrong, run `inspect_project.py`. It reports the registry count against the
panel count and flags four conditions: duplicate names, one file loaded twice, layers loaded
with no panel row, and broken sources. A clean report means name lookups are currently safe.

## The idea

The capture date currently lives only in layer *names*, which is why sorting imagery has
meant hand-building groups and themes that go stale the moment new scenes arrive. These
scripts promote the date to a queryable **attribute** (footprints) and a **temporal
property** (the layer itself). After that, two standard QGIS features do the real work:

- **Temporal Controller** (`View ► Panels ► Temporal Controller`) — a time slider that
  shows/hides imagery by date. Answers "what date am I looking at" continuously.
- **The footprints layer** — a thin index of coverage. Labelled by date and styled hollow,
  it tells you at a glance whether earlier/later imagery exists where you're zoomed in,
  without touching the Layers panel.

## Scope: what counts as "dated imagery"

Only discrete scenes with a real capture date — Planet/SkySat/Pelican/Vantor/Maxar and the
1999 aerials. Streaming service layers (NASA Landsat/OPERA/NISAR/Black Marble/Sentinel,
Esri Wayback, hillshade, OSM) are **deliberately excluded**: they are continuous or
composite products with no single capture instant, and giving them a nominal date would
make the time slider lie. They stay manual toggles.

Edit `SERVICE_MARKERS` in `imagery_index.py` if you want to change that call.

## Shared module

`imagery_index.py` holds the layer-name date parsing and the include/exclude rule, so all
three scripts agree on what a "dated scene" is. Change the rules in one place.
