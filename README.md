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

1. **Overview map** — post-event scene footprints over a terrain hillshade
2. **Scene picker** — table of scenes per location with date, sensor, cloud cover
3. **Compare map** — one map with a pinned **BEFORE / AFTER / TOPO** button bar:
   sub-meter pre-event imagery (Esri Wayback 2026-05-28), the 50 cm post-event scene,
   and an Esri World Hillshade terrain view — click BEFORE/AFTER to flicker
4. **Draw & export** — mark suspected landslides on the map and save them to
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

A ready-made QGIS project lives at **`qgis/geer_venezuela.qgz`** (relative paths, EPSG:4326).
It bundles the full layer stack, grouped and styled to match the notebooks: Basemaps
(Esri World Hillshade TOPO, sub-meter Esri Wayback 2026-05-28 BEFORE, the three 2026-06-26
Planet SkySat AFTER scenes for La Guaira streamed by URL), Terrain & Geology (slope in
inferno 0–45°, ≥30° steep outlines, geology filled by unit color with name/lithology map
tips), the USGS rapid assessment grid (extent-class fills, bold red outline where road
impacts = yes), Roads (arterials by class + magenta watch segments), and the labeled
landslide-candidate sites. BEFORE + AFTER + candidates are visible by default; toggle the
rest as needed. Note: the slope raster (`data/terrain/*.tif`) is gitignored — run
notebook 02 once to regenerate it, or the Slope layer will show as missing.

A **NASA Disasters (Earthdata)** group streams the agency's derived products live from ArcGIS
ImageServers (nothing downloaded): the **Sentinel-1 landslide proxy heatmap** (100 m, backscatter
change — coarse but blankets the whole Ávila massif and reaches inland sites the high-res optical
misses), Sentinel-2 (10 m) and Landsat optical, a Sentinel-2 building-damage likelihood raster,
OPERA and NISAR InSAR displacement (ground motion from the quake), and Black Marble night lights.
The **Vantor Legion** 0.42 m post-event mosaic from the same NASA folder is cached locally instead
(see below), since it's the one sub-meter optical product there. *Licensing:* Vantor imagery is
© Vantor and **non-redistributable** (NASA CSDA); the Sentinel-1 heatmap uses modified Copernicus
data and can show false positives (mining/construction/deforestation) — treat both as viewing
aids, not products to republish.

**All post-event high-res imagery is cached locally** in `data/basemaps/` (gitignored, ~10 GB)
and the project reads from those files — one flat **`AFTER — post-event imagery`** group holding
every post-event scene that intersects the USGS assessment extent (Puerto Cabello through
Independencia-Ocumare): the **15 Planet SkySat/Pelican scenes** across the six impacted locations,
plus the **Vantor Legion 0.42 m mosaic** (La Guaira, built from the ImageServer at native
resolution with the open-ocean tiles omitted so its NW corner is transparent). Layers are named
uniformly `AFTER — <location> · <sensor> <gsd>m · <id>`. Sensors: SkySat 0.66–0.87 m and the finer
Pelican ~0.62 m (only 4 Pelican scenes exist — 2 La Guaira, 2 Caracas). Maxar Open Data is not
activated for this event, so Planet + Vantor are the only sub-meter post-event sources.

The BEFORE (Wayback) and TOPO (hillshade) layers in the **Basemaps** group, and the whole NASA
Disasters group, still stream — they're tile/image services with no single file worth caching.
If `data/basemaps/` is empty (fresh clone) the AFTER layers show as missing: the SkySat/Pelican
`visual` COGs are public HTTPS downloads, and the Vantor mosaic is rebuilt by tiling the
ImageServer's `exportImage` endpoint.

Because streamed imagery can be slow to load, an **"Imagery footprints (toggle)"** layer at the
top of the tree draws a labeled, color-coded outline for every imagery layer's actual coverage
(cyan SkySat, magenta Pelican, yellow Vantor) — turn it on to see at a glance which scene covers
where before waiting for pixels. The two global tile basemaps (Wayback BEFORE, hillshade) cover
everywhere, so they have no footprint.

To add COGs manually instead — every COG opens directly in QGIS, no download:

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
notebooks/04_review_sites.ipynb      review/edit marked sites + KMZ export (GEER-style)
src/geer_venezuela/catalog.py        Planet/Source Coop catalog helpers
src/geer_venezuela/roads.py          OSM arterials + steep-slope watch segments
src/geer_venezuela/terrain.py        Copernicus DEM fetch, slope, steep areas
src/geer_venezuela/geology.py        Macrostrat/USGS geology fetch + point query
data/landslide_candidates/           exported GeoJSON for field teams
data/terrain/                        cached DEM/slope rasters + geology/steep GeoJSON
data/routes/                         watch segments, arterials, corridor summaries
data/usgs/                           USGS rapid landslide assessment (2026-07-01)
qgis/geer_venezuela.qgz              QGIS project bundling all layers, styled per notebooks
docs/field_recon_priorities.md       perishable-data priorities + recon best practices
PROGRESS.md                          running log of setup work
```
