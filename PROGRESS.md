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
- 12:05 — Notebook 01 restructured per Lorne's feedback: swipe section removed; flicker now has a
  **persistent one-click "Showing: AFTER/BEFORE" toggle** pinned to each map
  (`add_flicker_control` in `viewer.py`), on both the Planet and Wayback comparison maps.
  Kept his `LOCATION = "valencia"` selection. Re-verified headlessly end-to-end.
- 12:30 — Notebook 01 reworked again per feedback: Planet 4.8 m "before" dropped from the
  comparison (Wayback sub-meter is now the only BEFORE), and the flicker button became a
  three-way **BEFORE / AFTER / TOPO** switcher (`add_compare_control` in `viewer.py`).
  TOPO = Esri World Hillshade tiles (`HILLSHADE` in the package), also now the overview
  backdrop. Verified headlessly.
- 12:45 — Bug fix: `save_draw_features(..., indent=2)` crashed (kwarg forwarded to GDAL's
  GeoJSON writer as unknown option `INDENT`). Removed `indent=2` from every export cell in
  notebooks 01–03; GeoJSON write path re-verified.
- 13:00 — Queried Esri's Wayback metadata service for actual capture dates of the BEFORE
  imagery: mostly 2024 – early 2025 (Maxar WV02/WV03, GeoEye-1 at 0.3–0.5 m) across the
  corridor; Ocumare de la Costa is the outlier at Aug 2021. Added `wayback_capture_date(lat, lng)`
  helper for citing per-site before-dates.
- 14:35 — Added `04_review_sites.ipynb`: gathers every saved candidate GeoJSON onto one
  BEFORE/TOPO map and builds `site_list.csv` (per-site coordinates + before-image capture
  dates). Lorne has 44 features marked for La Guaira so far.
- 15:10 — Feature tagging built (`add_tagging_control` / `save_tagged_features` in `viewer.py`):
  pinned panel sets category + note, stamped onto each drawn feature; deletions untag.
  Notebook 01's marking flow now uses it. Review map (04) gained the missing AFTER view
  (scene ids parsed from candidate filenames) and the site table now carries tags.
  Confirmed: polygons were always saved correctly (CSV centroids caused the confusion).
- 15:40 — Review notebook gained a **site editor** (click a feature → retag or delete via
  pinned panel; `add_site_editor` in `viewer.py`) and a save cell that writes edits back to
  the per-source GeoJSONs **plus a `landslide_candidates.kmz`** (GEER's KML-product
  convention, via simplekml). Full select→retag→delete→save cycle tested; KMZ opens with
  44 placemarks named `site NNN — category`.
- 16:05 — Per Lorne: cleared all stored tags/notes from the candidate datasets (fresh start
  with his new Confidence/Priority tag scheme in `TAG_CATEGORIES`); KMZ placemarks renamed
  to site number only, with source/category/note moved to KML ExtendedData (structured
  metadata in the Google Earth balloon). Outputs regenerated and verified.
- 16:30 — Verified the two USGS GeoJSONs are the **same grid with identical values** (only a
  column name differs) — nothing was missing from the route map. Fixed hover metadata: the
  USGS layer was underneath the steep-area fill, which was eating mouse events; reordered
  layers and trimmed the attributes to `landslide_extent` + `road_impacts`.
- 2026-07-03 evening — Built `qgis/geer_venezuela.qgz` via the qgis-mcp plugin (relative
  paths, EPSG:4326): Basemaps (TOPO hillshade / Wayback 2026-05-28 BEFORE / three 2026-06-26
  SkySat AFTER COGs by URL), Terrain & Geology, USGS grid, Roads, and labeled candidate
  sites, all styled to match the notebooks; BEFORE+AFTER+candidates on by default. Verified
  by rendering the canvas. Two QGIS gotchas hit and solved: (1) QGIS silently re-set the
  project CRS to the first layer's UTM zone — had to re-apply EPSG:4326 after adding layers;
  (2) Wayback tile requests 301-redirect (relative `Location`) to the release actually
  holding each tile, which QGIS-LTR's tile fetcher can't follow — served the BEFORE layer
  through GDAL's TMS driver (libcurl follows redirects) instead of a QGIS XYZ layer.
  Candidate labels use `$id`, verified to match `site_no` in `site_list.csv` (0–43).
- 2026-07-04 — Added NASA Earthdata (Disasters Program) services to `geer_venezuela.qgz`,
  streamed live from the `DISASTERS_202606_EARTHQUAKE_VENEZUELA` ArcGIS ImageServers via
  the `arcgismapserver` provider (no download). (1) **Vantor Legion** 0.42 m true-color
  mosaic (post-event 2026-06-25) into Basemaps, below the SkySat strips so the narrow SkySat
  swaths render on top and the mosaic fills the coastal gaps around them. Coverage is a
  ~20×16 km **coastal band only** (lat 10.51–10.65°N): contains 29/44 candidate points and
  4/18 areas — the inland sites climbing south up the Ávila fall just below its footprint.
  (2) **Sentinel-1 landslide proxy heatmap** (NASA GSFC, 100 m, Iratio backscatter change
  pre vs 2026-06-25) into a new "NASA Disasters (Earthdata)" group — covers the whole massif
  (all 44 points + 18 areas), off by default at 70% opacity; it's the inland-site companion
  the Vantor mosaic can't provide. Licensing note: Vantor imagery is © Vantor / non-
  redistributable (NASA CSDA); the S1 heatmap contains modified Copernicus Sentinel data and
  can throw false positives (mining/construction/deforestation). Then added the remaining
  Earthdata siblings to the NASA Disasters group (all off by default): sentinel2 (10 m optical,
  whole region), landsat (30 m optical), sentinel2_buildingDamageLikelihood (10 m), OPERA and
  NISAR LOS displacement (InSAR ground motion), and Black Marble night lights. Only the slope
  `.tif` is on disk — every imagery/raster service (SkySat, Vantor, Wayback, hillshade, and the
  7 NASA ImageServers) streams live via `/vsicurl/`, GDAL TMS, XYZ, or `arcgismapserver`.
- 2026-07-04 — Basemap sizes / downloadability checked: the two Planet SkySat `visual` COGs are
  786 MiB and 862 MiB (public HTTPS, directly downloadable / `gdal_translate` a window). Vantor
  ImageServer capabilities = "Image,Metadata,Catalog" (no Download service) but exportImage works
  (max 15000×4100 px/request, U16 8-band) — pull it in tiles or via QGIS Export→Save As. Wayback
  and hillshade are tile services (no source file); "download" = render the AOI to a local GeoTIFF
  at a chosen zoom. QGIS layer → Export → Save As is the universal path for any remote layer.
- 2026-07-04 — Cached the AFTER imagery locally to `data/basemaps/` (gitignored) and repointed the
  QGIS project at the local files (policy: use local COG where we have one, keep "AFTER" in the
  layer name, stream only what we don't). Standing project convention now.
  - Two SkySat `visual` COGs curl'd directly (786 / 862 MiB) → layers renamed `AFTER — Planet
    SkySat … (local)`. Confirmed native 0.5 m with full overview pyramids (an earlier "looks
    low-res" was just a macOS Preview thumbnail / zoomed-out view).
  - Vantor mosaic (no Download service) pulled via `exportImage` `f=json`→href tiling at native
    0.42 m, `format=png` (NOT `tiff`, which returns the raw 8-band U16 analytic ~440 MB/tile),
    georeferenced from the returned extent. Skipped the 18 open-ocean grid cells (of 60) after
    reading a full-extent overview — coast runs SW→NE, whole NW is Caribbean. Mosaicked the 42
    land/coast tiles with `gdalbuildvrt -addalpha` (ocean gap → transparent) into a 251 MiB JPEG
    COG (`vantor_legion_20260625_mosaic.tif`). Layer: `AFTER — Vantor Legion … (mosaic, local)`.
  - Gotchas: system GDAL 3.3.3 (Postgres.app) has **no JPEG codec** — can't write *or read* JPEG
    COGs; used rasterio's bundled GDAL 3.12 to build it (QGIS's own GDAL reads it fine). Python
    `urllib` fails macOS TLS (no CA bundle) → shelled out to `curl`. NASA ImageServer 503s under
    sustained load (render times ballooned to 3–7 min/tile); the fetch script is resumable with
    backed-off retries. `data/basemaps/` totals ~1.9 GB (SkySat 1.6 GB + Vantor 251 MiB).
- 2026-07-05 — Expanded post-event coverage to the whole **USGS rapid-assessment AOI** (bbox
  −68.50→−66.61 lon, 10.19→10.63 lat; ~205 km of coast, Puerto Cabello → Independencia-Ocumare).
  Of the 17 Planet post-event scenes, **15 intersect the AOI** (2 excluded: Yumare far west + one
  ocean-only La Guaira pass). Added the **13 not already cached** as remote `/vsicurl/` COG layers,
  grouped by location in a new "AFTER — post-event scenes (AOI)" group, all **off by default**
  (13 streaming COGs at once is brutal). Sensors: SkySat 0.66–0.87 m + Pelican 0.62–0.65 m — the
  only post-event sub-meter optical available. **Maxar Open Data still NOT activated** for this
  event (rechecked their full STAC — no Venezuela/2026-06 entry); no other high-res post-event source.
- 2026-07-05 — Added a toggleable **"Imagery footprints (toggle)"** layer at the top of the tree
  (off by default) so imagery coverage is legible without waiting for slow COG/tile loads. One
  outline-only polygon per imagery layer (15 Planet scene footprints from the catalog geometry +
  the Vantor land/coast staircase), categorized by sensor (cyan SkySat / magenta Pelican / yellow
  Vantor), labeled `location · sensor · gsd · date`. Source: `data/basemaps/imagery_footprints.geojson`
  (gitignored; regenerate with the build_footprints catalog query). Global tile basemaps (Wayback
  BEFORE, TOPO hillshade) have no footprint — they cover everywhere.
- 2026-07-05 — Cached **all 15 AOI Planet scenes** locally (8.1 GB new; `data/basemaps/` now ~10 GB)
  and consolidated the imagery. Fixed a mislabel: the two La Guaira "SkySat" scenes are actually
  **Pelican** (0.62 m) — corrected both the on-disk filenames (`skysat_*`→`pelican_*`) and the layer
  names. All post-event imagery (15 scenes + Vantor) now lives in **one flat `AFTER — post-event
  imagery` group**, all local, uniformly named `AFTER — <location> · <sensor> <gsd>m · <id>`, ordered
  by location; the old per-location "AOI" subgroups are gone. Basemaps group keeps only the remote
  context layers (BEFORE Wayback, TOPO hillshade). Per Lorne: the AOI is uniform — no location is
  "primary" (La Guaira was just first to have data), and layer on/off is his to toggle (don't design
  around default visibility). Only 4 Pelican scenes exist (2 La Guaira, 2 Caracas) — the finest optical.
- 2026-07-05 — Candidate sites cleanup + numbering. The site numbers were only `$id` labels
  (`to_string($id)`), not a field — invisible in the attribute table, and running backwards
  because uncommitted features get negative decreasing fids. Lorne had also grown the layer to
  the whole AOI and manually replaced the polygons with points near their centroids. Found the
  file still held 103 points + 18 polygons + 1 null-geom (122) — his polygon deletions never
  committed (the two geometry-filtered layers on one GeoJSON is fragile). Checked each polygon
  for a replacement point: 17/18 had one within 6–60 m; 1 orphan (~263 m) → converted to a point.
  Result: a real integer `site_no` field, **104 points numbered 1–104** in file order (groups kept
  together), labeled by `site_no`; dropped the 17 redundant polygons + null; removed the empty
  polygons layer; renamed the layer to **"Candidate sites"**. (`site_list.csv` is now stale — regen
  via notebook 04; the file is still misnamed `la-guaira_…_3010.geojson` but holds AOI-wide points.)
  **Gotcha:** editing the GeoJSON on disk while QGIS had it open got **clobbered** — QGIS flushed
  its cached copy back over the write, and `reload()`/`setDataSource()` kept serving the stale
  cache. Fix: remove all layers referencing the file first (releases OGR's handle), THEN edit on
  disk, THEN re-add a fresh layer. Backup of the 122-feature pre-edit state is in the scratchpad.
