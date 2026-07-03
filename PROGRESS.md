# GEER Venezuela — setup progress

Goal: local (VSCode) workflow to compare pre-earthquake quarterly basemaps against post-earthquake
Planet imagery for the 2026-06-24 Venezuela earthquakes, to spot landslide evidence and flag
areas for field teams.

## Plan

1. ✅ Scout the Source Cooperative dataset structure
2. ✅ Scaffold uv project + dependencies
3. ✅ Helper module for the STAC/GeoParquet catalog (`src/geer_venezuela/catalog.py`)
4. ✅ Notebook `notebooks/01_compare_imagery.ipynb` — overview map, before/after split map,
   layer-toggle flicker, draw & export landslide-candidate points to GeoJSON
5. ✅ README with usage + QGIS fallback instructions
6. ✅ End-to-end verification — notebook executed headlessly with zero errors

## What I learned about the data

- Everything is public HTTPS COGs under `https://data.source.coop/planet/venezuela-earthquake-2026-06-24/`
  with a STAC catalog + GeoParquet indexes (`pre-event/items.parquet`, `post-event/items.parquet`).
- **Pre-event**: Planet Q1 2026 quarterly basemap, ~4.8 m RGB — 40 tiles *plus one merged COG*
  (`quarterly-mosaic-2026Q1_display.tif`) which we use as the single "before" layer.
- **Post-event**: 17 SkySat/Pelican scenes at 50 cm, 26–28 June 2026, across 7 locations:
  Caracas (3), Catia La Mar (1), Independencia & Ocumare (1), La Guaira (8), Puerto Cabello (2),
  Valencia (1), Yumare (1). Assets per scene: `visual` (RGB), `analytic` (4-band), `udm2` (cloud mask).
- License: CC BY-NC 4.0, © Planet Labs PBC.

## Decisions

- **Viewing platform**: Jupyter notebook in VSCode with `leafmap` — streams COG tiles via
  titiler.xyz, no downloads needed. Split-map swipe + layer checkbox flicker for before/after.
  QGIS works too (COGs open directly via URL); documented as fallback in README.
- Resolution mismatch to keep in mind: pre-event is 4.8 m, post-event is 0.5 m — small landslides
  will only be visible in the "after" image; the "before" tells you whether a scar is new.

## Phase 2 — terrain + geology (2026-07-03, in progress)

Goal: slope layer from a DEM to target steep terrain, plus surface geology.

- ✅ **DEM source chosen**: Copernicus GLO-30 (30 m global, free) — public COGs on AWS
  (`copernicus-dem-30m` bucket), verified reachable. Will stream windowed reads per location,
  reproject to UTM 19N, compute slope, save local COGs.
- ✅ **Geology source chosen**: USGS *Geologic Map of Venezuela* 1:750k (Hackley, Urbani et al.)
  via **Macrostrat** vector tiles/API (CC-BY). USGS's own GIS release (DS-199) is a 2006 ESRI
  personal geodatabase (.mdb) — unreadable on macOS, so Macrostrat is the practical route to
  the same polygons; verified MVT tiles decode with name/lithology/age attributes.
- ✅ Built `terrain.py` (fetch_dem / compute_slope / steep_areas) and `geology.py`
  (fetch_geology polygons, geology_at point query, Macrostrat tile URL).
- ✅ Notebook `02_terrain_geology.ipynb` — slope raster + steep-area outlines (≥30°) +
  geology polygons over the post-event imagery, with GeoJSON exports for field teams.
  Executed headlessly end-to-end for La Guaira: mean slope 13°, 14% of AOI ≥ 30°,
  units include the Tacagua Schist / Ávila Suite (the 1999 Vargas debris-flow lithologies).
- Rejected: USGS DS-199 geodatabase download (2006 .mdb, unreadable on macOS);
  OpenTopography API (needs an API key; Copernicus AWS bucket doesn't).

## Phase 3 — roads, routes, recon priorities (2026-07-03, in progress)

- ✅ **Road source chosen**: OpenStreetMap via Overpass/osmnx — `highway` tag gives functional
  class directly (arterials = motorway/trunk/primary/secondary). Network is rich here
  (both Caracas–La Guaira autopistas, Avenida Boyacá, Galipán road all present).
- ✅ `roads.py`: `fetch_roads()` + `watch_segments()` — arterial segments within 100 m of
  ≥30° slopes. La Guaira AOI: 144 km of watch segments; top corridors are exactly the
  critical lifelines (Autopista + Carretera Vieja Caracas–La Guaira, Av. Boyacá).
- ✅ Notebook `03_route_planning.ipynb` — route map (roads by class, bold watch segments,
  candidate sites, draw-your-route) + GeoJSON/CSV exports to `data/routes/`. Verified headlessly.
- ✅ **Major find**: USGS already runs a landslide response for this event with a provisional
  triage grid (DOI 10.5066/P1MRLOZ7) — downloaded to `data/usgs/`, added to the route map
  (extent class + road-impact flags per ~4 km cell; 141 cells in the La Guaira AOI).
- ✅ `docs/field_recon_priorities.md` — Lorne's perishability notes reviewed against the GEER
  manual v4, Kaikōura 2016 literature, and USGS/EERI guidance. Two additions rank above
  everything in the draft: landslide dams / impounded water (life-safety, hours–days) and
  debris on corridors before clearing (days). Also added: doublet timing attribution via
  witnesses/media, pre-first-rain acquisition urgency, and GEER product conventions
  (2-week web report, filterable site/photo/observation structure, DesignSafe archiving).
- ⬜ Later: shareable web/PDF report of site-visit recommendations (deferred by design).

## Status log

- 09:45 — Dataset scouted, uv project created, deps installed (leafmap, geopandas, duckdb, rasterio, jupyter).
- 09:55 — Catalog helpers written and smoke-tested against live data (17 post scenes, 40 pre tiles load correctly).
- 09:58 — Verified leafmap split_map streams remote COGs and zooms to the right-hand (post-event) layer. Now writing the notebook.
- 10:05 — Notebook written and executed headlessly end-to-end: all maps build, no errors. Writing README next.
- 10:10 — README done, project metadata cleaned up. **Setup complete** — open
  `notebooks/01_compare_imagery.ipynb` in VSCode, pick the `.venv` kernel, run all cells.
- 10:20 — Phase 2: DEM + geology sources verified (Copernicus GLO-30 on AWS; Macrostrat
  serving the USGS 1:750k Venezuela map). USGS's own GIS release is a dead end on macOS.
- 10:35 — Terrain + geology helpers and notebook 02 written, executed headlessly, all green.
  **Phase 2 complete.**
- 11:00 — Phase 3: OSM arterials + watch segments built and verified; research agent digging
  through GEER/Kaikōura literature in parallel.
- 11:20 — USGS event dataset found and integrated into the route map; notebook 03 verified
  end-to-end; recon-priorities doc written. **Phase 3 complete.**
- 11:45 — Answered "is Google Earth's hi-res pre-event imagery open?" — no (licensed, screenshots
  with attribution only), but **Esri World Imagery Wayback release 2026-05-28** is the legit
  equivalent: sub-meter public tiles, verified over the Ávila. Added as section 6 of notebook 01
  (`WAYBACK_PRE_EVENT` in the package). Maxar Open Data NOT activated for this event yet — recheck.
