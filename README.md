# GEER Venezuela — 2026-06-24 earthquake imagery reconnaissance

A **QGIS** reconnaissance project for identifying landslide evidence along the Venezuela coast
after the 2026-06-24 earthquakes and flagging sites for field investigation. Pre-earthquake
sub-meter imagery is compared against post-earthquake high-resolution imagery, with terrain,
geology, roads, and the USGS rapid landslide assessment as targeting layers.

Everything lives in one QGIS project: **`qgis/geer_venezuela.qgz`** (EPSG:4326, relative paths).
Open it in QGIS 3.x (LTR). The work is done interactively — often driven through Claude Code via
the [qgis-mcp](#working-through-claude-qgis-mcp) plugin.

Imagery data: [Planet Crisis Response on Source Cooperative](https://source.coop/planet/venezuela-earthquake-2026-06-24)
(© Planet Labs PBC, **CC BY-NC 4.0**), plus NASA Earthdata Disasters products and Esri World
Imagery Wayback — see [Data & licensing](#data--licensing).

## Quick start

1. Install QGIS 3.x (LTR) and, for local imagery, run `uv sync` once (the `src/` helpers that
   fetch/refresh data need the Python env; QGIS itself does not).
2. Open **`qgis/geer_venezuela.qgz`**.
3. If any **`AFTER — post-event imagery`** layers show as missing, the local basemap cache
   (`data/basemaps/`, gitignored, ~10 GB) hasn't been populated on this machine — see
   [Refreshing / extending data](#refreshing--extending-the-data).

## What's in the project

Layer tree, top to bottom:

- **Imagery footprints (toggle)** — labeled, color-coded outlines of every imagery layer's actual
  coverage (cyan SkySat, magenta Pelican, yellow Vantor). Turn it on to see at a glance which
  scene covers where *before* waiting for pixels to stream/load.
- **Candidates → Candidate sites** — the marked landslide points, each with an integer **`site_no`**
  attribute (labeled on the map). Digitize new points here (see [Marking sites](#marking-candidate-sites)).
- **Roads** — OSM arterials colored by class + magenta **watch segments** (arterial stretches
  within 100 m of ≥30° slopes, where teams should scan for cracking/rockfall).
- **NASA Disasters (Earthdata)** — streamed live from ArcGIS ImageServers (nothing downloaded):
  Sentinel-1 landslide proxy heatmap (100 m — coarse but blankets the whole Ávila massif),
  Sentinel-2 (10 m) and Landsat optical, Sentinel-2 building-damage likelihood, OPERA and NISAR
  InSAR displacement (ground motion from the quake), and Black Marble night lights.
- **USGS** — the [rapid landslide assessment](https://doi.org/10.5066/P1MRLOZ7) triage grid
  (extent-class fills, bold red outline where road impacts = yes). Its extent defines the AOI.
- **Terrain & Geology** — slope from the Copernicus GLO-30 DEM (inferno 0–45°), ≥30° steep-area
  outlines, and surface geology from Macrostrat/[USGS 1:750k](https://pubs.usgs.gov/of/2005/1038/)
  (unit name, lithology, age in the attributes).
- **AFTER — post-event imagery** — all **15 Planet SkySat/Pelican scenes** that intersect the AOI
  (six locations, Puerto Cabello → Independencia-Ocumare) plus the **Vantor Legion 0.42 m mosaic**
  (La Guaira). Cached locally as COGs; named uniformly `AFTER — <location> · <sensor> <gsd>m · <id>`.
  SkySat is 0.66–0.87 m; the finer **Pelican** (~0.62 m) exists for only 4 scenes (2 La Guaira,
  2 Caracas). Maxar Open Data is not activated for this event, so Planet + Vantor are the only
  sub-meter post-event sources.
- **Basemaps** — the streamed context layers: **BEFORE** = Esri World Imagery Wayback release
  2026-05-28 (sub-meter pre-event), and **TOPO** = Esri World Hillshade.

Layer on/off is yours to toggle as needed — there's no fixed "default view."

### Local imagery cache

All post-event AFTER imagery reads from local COGs in **`data/basemaps/`** (gitignored, ~10 GB) so
it renders fast. The BEFORE (Wayback) and TOPO (hillshade) basemaps and the entire NASA Disasters
group stream live — they're tile/image services with no single file worth caching. The Vantor
mosaic was built by tiling its ArcGIS `exportImage` endpoint at native resolution, with the
open-ocean tiles omitted (its NW corner is transparent). *Licensing:* Vantor imagery is © Vantor
and **non-redistributable** (NASA CSDA); the Sentinel-1 heatmap uses modified Copernicus data and
can show false positives (mining/construction/deforestation) — treat both as viewing aids, not
products to republish.

## Working through Claude (qgis-mcp)

This project is driven interactively through **Claude Code** using the **qgis-mcp** plugin, which
exposes the running QGIS instance to Claude over a local socket (port 9876). To enable it:

1. Install the qgis-mcp plugin in QGIS and open `qgis/geer_venezuela.qgz`.
2. Open the qgis-mcp dock, click **Start Server** (it must be started by hand each session).
3. In Claude Code, ask for what you want — Claude can add/style layers, run identify/queries,
   render the canvas, build print layouts, fetch and cache imagery, and digitize/renumber
   features, all against the live project.

**Caveat:** don't have Claude (or any external tool) edit a data file while QGIS has it open —
QGIS caches the file and can flush its copy back over the external write. Remove the layer first,
edit, then re-add.

## Marking candidate sites

Toggle a BEFORE/AFTER pair (e.g. Wayback vs a Pelican scene over the same area — the footprints
layer shows which scene covers where), and digitize points into the **Candidate sites** layer.
Each point carries `site_no` (renumber 1…N if you add/remove a batch) plus `category`/`note`
fields for confidence and observations. The layer exports directly to GeoJSON/KMZ for field handoff.

## Data & licensing

| | Pre-event (BEFORE) | Post-event (AFTER) |
|---|---|---|
| Source | Esri Wayback 2026-05-28 (Maxar/GeoEye) | Planet SkySat + Pelican; NASA Vantor Legion |
| Resolution | ~0.3–0.5 m | 0.42–0.87 m |
| Dates | 2024 – early 2025 (varies by tile) | 25–28 June 2026 |
| Coverage | global tiles | 15 Planet scenes over 6 AOI locations + 1 mosaic |

AOI locations: Puerto Cabello, Catia La Mar, Valencia, La Guaira, Caracas, Independencia & Ocumare
de la Costa. (Planet also imaged Yumare, outside the USGS AOI.) A ~4.8 m Planet quarterly mosaic
covers the whole coast as an optional coarse pre-event backdrop but isn't in the project by default.

## Refreshing / extending the data

The `src/geer_venezuela/` helpers fetch and process the source data — run them with
`uv run python` (they produced the layers already in the project; rerun to update or add locations):

```
src/geer_venezuela/catalog.py   Planet/Source Coop STAC catalog — scenes, footprints, COG URLs
src/geer_venezuela/terrain.py   Copernicus GLO-30 DEM → slope + ≥30° steep areas
src/geer_venezuela/geology.py   Macrostrat / USGS 1:750k geology (fetch + point query)
src/geer_venezuela/roads.py     OSM arterials + steep-slope watch segments
```

The SkySat/Pelican `visual` COGs are public HTTPS downloads (catalog helpers give the URLs); the
Vantor mosaic is rebuilt by tiling the NASA ImageServer's `exportImage` endpoint.

## Field-team guidance & deliverable

`docs/field_recon_priorities.md` is a perishable-data priority ranking (landslide dams first,
corridor debris before clearing, crown cracking, timing attribution, pre-first-rain baselines),
reviewed against the GEER manual and Kaikōura 2016 response literature, with capture protocols and
report conventions.

The **shareable product for field teams is still to be decided** — candidate options include a
QGIS print-layout **atlas → PDF** (one page per site with map + attributes), a **KMZ** for Google
Earth / mobile, or a **web/PDF report**. `bare_bones.md` and `_temp.md` hold working notes toward it.

## Layout

```
qgis/geer_venezuela.qgz          the QGIS project — all layers, styled
src/geer_venezuela/catalog.py    Planet/Source Coop catalog helpers
src/geer_venezuela/roads.py      OSM arterials + steep-slope watch segments
src/geer_venezuela/terrain.py    Copernicus DEM fetch, slope, steep areas
src/geer_venezuela/geology.py    Macrostrat/USGS geology fetch + point query
data/basemaps/                   local COG cache: post-event AFTER imagery + footprints (gitignored)
data/landslide_candidates/       marked candidate sites (GeoJSON, KMZ)
data/terrain/                    cached DEM/slope rasters + geology/steep GeoJSON
data/routes/                     watch segments, arterials, corridor summaries
data/usgs/                       USGS rapid landslide assessment (2026-07-01)
docs/field_recon_priorities.md   perishable-data priorities + recon best practices
PROGRESS.md                      running log of setup work
```
