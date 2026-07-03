# GEER Venezuela — 2026-06-24 earthquake imagery reconnaissance

Local workflow for comparing **pre-earthquake** Planet quarterly basemaps against
**post-earthquake** high-resolution imagery of the Venezuela coast, to identify landslide
evidence and flag areas for field investigation.

Data: [Planet Crisis Response on Source Cooperative](https://source.coop/planet/venezuela-earthquake-2026-06-24)
— imagery © Planet Labs PBC, licensed **CC BY-NC 4.0** (non-commercial, attribution required).

## Quick start

```bash
uv sync
```

Then open `notebooks/01_compare_imagery.ipynb` in VSCode and select the `.venv` Python
environment as the kernel (VSCode will suggest it). Run cells top to bottom.

The notebook gives you:

1. **Overview map** — post-event scene footprints over the pre-event basemap
2. **Scene picker** — table of scenes per location with date, sensor, cloud cover
3. **Before/after swipe map** — drag a divider between pre and post imagery
4. **Flicker map** — both layers stacked; toggle the AFTER layer on/off to make new
   landslide scars pop out
5. **Draw & export** — mark suspected landslides on the map and save them to
   `data/landslide_candidates/*.geojson` to hand to field teams

Nothing is downloaded — imagery streams as tiles from cloud-optimized GeoTIFFs (COGs) on
`data.source.coop`, so you need an internet connection. Tiling goes through the public
[titiler.xyz](https://titiler.xyz) service (leafmap's default).

A second notebook, `notebooks/02_terrain_geology.ipynb`, adds **targeting layers**:

- **Slope** from the Copernicus GLO-30 DEM (30 m, © DLR/ESA, AWS Open Data) — clipped per
  location, reprojected to UTM 19N, cached in `data/terrain/`; red outlines mark areas ≥ 30°
- **Surface geology** from Macrostrat (CC-BY), which here serves the digitized
  [USGS Geologic Map of Venezuela 1:750k](https://pubs.usgs.gov/of/2005/1038/)
  (Hackley, Urbani, Karlsen & Garrity) — polygons with unit name, lithology, and age
- GeoJSON exports of steep areas and geology for QGIS / field handoff

A third notebook, `notebooks/03_route_planning.ipynb`, builds the **field route map**:

- Arterial roads from OpenStreetMap (© OSM contributors, ODbL), colored by class
- **Watch segments** — arterial stretches within 100 m of ≥30° slopes, where teams should
  drive slowly and scan for cracking/rockfall (La Guaira: 144 km, led by both
  Caracas–La Guaira highways and Avenida Boyacá)
- Landslide-candidate sites from the other notebooks, plus draw-your-own route
- The **USGS rapid landslide assessment** for this event (provisional triage grid,
  [DOI 10.5066/P1MRLOZ7](https://doi.org/10.5066/P1MRLOZ7), cached in `data/usgs/`)
- Exports to `data/routes/` (GeoJSON + corridor summary CSV)

Field-team guidance lives in `docs/field_recon_priorities.md` — a perishable-data priority
ranking (landslide dams first, corridor debris before clearing, crown cracking, timing
attribution, pre-first-rain baselines) reviewed against the GEER manual and Kaikōura 2016
response literature, with capture protocols and report conventions.

## The data

| | Pre-event | Post-event |
|---|---|---|
| Source | Planet quarterly basemap, Q1 2026 | SkySat + Pelican collects |
| Resolution | ~4.8 m | 50 cm |
| Dates | Jan–Mar 2026 composite | 26–28 June 2026 |
| Coverage | Whole affected coast (one merged COG) | 17 scenes over 7 locations |
| Assets | RGB | `visual` (RGB), `analytic` (BGRN), `udm2` (cloud mask) |

Locations: Caracas, Catia La Mar, Independencia & Ocumare de la Costa, La Guaira,
Puerto Cabello, Valencia, Yumare.

Catalog access helpers live in `src/geer_venezuela/catalog.py` (STAC-GeoParquet indexes
queried with DuckDB; returns GeoDataFrames).

## Using QGIS instead

Every COG opens directly in QGIS — no download:

1. **Layer → Add Layer → Add Raster Layer**, set *Source type* to **Protocol: HTTP(S)**
2. Paste a COG URL, e.g. the pre-event mosaic:
   `https://data.source.coop/planet/venezuela-earthquake-2026-06-24/pre-event/quarterly-mosaic/quarterly-mosaic-2026Q1_display.tif`
3. Add a post-event `visual` COG the same way (get URLs from the notebook's scene table,
   or browse the [dataset page](https://source.coop/planet/venezuela-earthquake-2026-06-24)),
   then toggle layer visibility to compare.

The exported `data/landslide_candidates/*.geojson` files load directly in QGIS and
ArcGIS Online.

## Layout

```
notebooks/01_compare_imagery.ipynb   before/after imagery comparison
notebooks/02_terrain_geology.ipynb   slope + geology targeting layers
notebooks/03_route_planning.ipynb    arterials + watch segments + route export
src/geer_venezuela/catalog.py        Planet/Source Coop catalog helpers
src/geer_venezuela/roads.py          OSM arterials + steep-slope watch segments
src/geer_venezuela/terrain.py        Copernicus DEM fetch, slope, steep areas
src/geer_venezuela/geology.py        Macrostrat/USGS geology fetch + point query
data/landslide_candidates/           exported GeoJSON for field teams
data/terrain/                        cached DEM/slope rasters + geology/steep GeoJSON
data/routes/                         watch segments, arterials, corridor summaries
data/usgs/                           USGS rapid landslide assessment (2026-07-01)
docs/field_recon_priorities.md       perishable-data priorities + recon best practices
PROGRESS.md                          running log of setup work
```
