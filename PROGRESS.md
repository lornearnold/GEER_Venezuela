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
- 2026-07-05 — **Pivoted from notebooks to a QGIS-only workflow** (driven through Claude via the
  qgis-mcp plugin). Deleted `notebooks/` (01–04 + cache; committed & pushed in `moving to qgis`
  first). Rewrote README to be QGIS-first (project layout, qgis-mcp setup, marking sites, data
  refresh via `src/` helpers). The `src/` data helpers (catalog/terrain/geology/roads) stay useful
  for fetching/updating; **`src/geer_venezuela/viewer.py` is now orphaned** (leafmap/ipywidgets UI,
  notebook-only) along with its `__init__.py` re-exports and the notebook-only deps in
  `pyproject.toml` (jupyter, leafmap, ipykernel, ipywidgets, localtileserver, simplekml) — left in
  place, flagged for a follow-up cleanup. Field-team deliverable format still undecided.
- 2026-07-05 — Added attribute fields to **Candidate sites** (via QGIS edit-session commit, not a
  disk edit): `perishability`, `location`, `extent`, `group` (String), `road_dist_m` (Double, empty).
  Set **Value Map** edit widgets (dropdowns, stored==displayed) on the first three:
  perishability=high/med/low, location=remote/populated, extent=large/medium/small. `group` is open
  text for clustering points into drone-flyover "sites" (filter/categorize by it). `road_dist_m` is
  a placeholder for straight-line distance to the nearest drivable road (walk-in gap for a drone
  team) — NOT yet populated; the arterials layer is arterials-only (no side streets), so the plan is
  to re-pull the FULL OSM drivable network (extend `roads.py`), auto-compute nearest-road distance,
  and hand-refine the remote (>~200 m) sites against the 0.5 m imagery.
- 2026-07-05 — **Populated `road_dist_m`** for all 110 candidate sites = straight-line distance to
  the nearest *drivable* road (the drone walk-in gap for a driving team). The arterials layer was
  motorway/trunk/primary/secondary only (~4k lines); re-pulled the FULL OSM drivable network via
  osmnx `features_from_bbox` over the AOI + ~3 km pad — classes motorway…living_street **+ service**
  (no unpaved `track`, per Lorne), `_link` ramps folded in → **21,653 lines**, saved to
  `data/routes/la-guaira_drivable.geojson` and added as **"Drivable roads (OSM)"** (thin grey) at the
  bottom of the Roads group. Distance computed point→nearest-line in **EPSG:32619 (UTM 19N)**, rounded
  to the nearest **10 m** (per the "no finer than 10 m" spec). Distribution: 38 sites ≤50 m, 19 in
  51–100, 24 in 101–250, 9 in 251–500, 20 >500 m (max 2230 m — remote hillside sites to hand-refine).
  Written **through QGIS** (edit-session/provider commit, not a disk edit — the file was open).
  **Field-type fix:** `road_dist_m` had been created as **String** (not the Double the prior note
  claimed); converted in place to **Integer** via the OGR provider (delete+add+repopulate) so numeric
  filters like `road_dist_m > 200` and graduated symbology work. Compute script:
  `scratchpad/road_dist.py`.
- 2026-07-05 — **Drafted Typst one-page site-summary template** (`reports/site_summary.typ`, compiles
  with typst 0.14; output `reports/site_summary.pdf`). One page per group: header (group name +
  location + site count; GEER banner right), main figure = highest-res AFTER imagery with candidate
  points labeled by `site_no`, locator inset (hillshade + arterials + red extent box at 1:75k),
  scale bar + north arrow overlays, then a site table (site_no, perishability, extent, WGS84
  coords, road_dist_m, notes — `group` lives in the header, not the table) + footnote defining the
  fields. Figures rendered headlessly from QGIS via `QgsMapRendererParallelJob` (EPSG:32619, 300 dpi,
  labels on) into `reports/figures/`. Examples: **Trocha** (7 sites; E–W spread 765 m forced
  **1:6000**, outside the 1:1000–1:5000 spec per the "increase if it doesn't fit" rule) and
  **site 94** (1:2000 main + 1:3000 alternative page for review). Imagery pick: vantor 0.42m does
  NOT cover either target; **pelican 0.62m 20260626_150535** covers both (site 94 sits on its scene
  edge — nodata corner filled by underlaying skysat 0.67m u0002, faint seam). Footprints layer's
  `already_local` attr is stale (said skysat u0002 not local; it is). Next: pick s94 scale, then
  script per-group data+figure generation for all 11 groups/60 ungrouped sites.
- 2026-07-05 — **Site-summary template v2** (`reports/site_summary.typ`): Arial; all layout numbers
  hoisted to named variables at the top of the file; table content no longer typed in Typst — a new
  `reports/export_site_data.py` dumps the candidates layer to `reports/site_data.json` (110 sites)
  and pages reference `group: "Trocha"` / `site-nos: (94,)` only; coordinates are Google-Maps
  hyperlinks (`maps/search/?api=1&query=lat,lon`). Locator inset switched to **Google Maps tiles at
  1:300k** (variant H; box offset north so the coast shows; thin 0.4 mm red box; © Google
  attribution in caption — license check needed before public distribution). **Header-overflow
  cause found:** Typst draws `header:` inside the top margin; the two-line header (~0.55 in) was
  taller than the 0.55 in margin minus the default 30% header-ascent, so it spilled toward the
  paper edge — fixed with `margin-top: 1.05in` + explicit `header-ascent`. Typst gotcha: a
  multi-line method chain after `#let x = expr` silently stops parsing at the line break (the
  `.map(...)` never ran → type error downstream); wrap the chain in parentheses. Locator variant
  review sheet kept at `reports/locator_variants.typ` (A–H).
- 2026-07-05 — Site summaries: locator inset scale is now **50× the main figure scale**
  (`locator-mult` variable; caption computes it) — Trocha 1:6000→1:300k unchanged, site 94
  1:2000→1:100k / 1:3000→1:150k (new centered renders in `reports/figures/`). **Fixed the
  Google-Maps links:** Typst's `str()` renders negative numbers with a Unicode minus (U+2212),
  which Google can't parse as a longitude — build URL numbers with an ASCII "-" (`url-dd()`)
  and encode the comma as %2C. Verified the embedded PDF URIs decode clean (Typst stores them
  hex-encoded: `/URI <68747470...>`, so grep for hex, not literal strings).
- 2026-07-05 — **Built the full field packet** (`reports/report.pdf`, 38 pp): cover + 36 priority-
  ordered unit pages (10 groups + 25 ungrouped singles + 1 bundle). Pipeline: plan built in QGIS
  (`reports/report_plan.json`) — units classified into sections (2: high perish/populated,
  3: med/populated by extent, 4: med/remote by extent, 5: rest incl. high/remote, 6: the 35
  ungrouped low-confidence sites as ONE bundle at 1:150k on Google basemap); per-unit extent →
  scale ladder (singles 1:2000; groups up to 1:20k); imagery pick = lowest-GSD footprint containing
  the extent (vantor mosaic verified by 9-pt raster sampling — bbox includes nodata; footprints
  layer carries a STALE vantor layer_name 'AFTER — Vantor Legion…' needing an alias) + underlay
  when partial. All figs/locators rendered headlessly (~75 renders; MCP socket times out at 60 s
  but QGIS keeps executing — poll the output dir). Typst refactored: `template.typ` (defs +
  `title:`/`locator-scale:` params) imported by `report.typ` (cover: coverage map w/ used-scene
  footprints + dead zone, aggregated imagery-sources table, notes) and `site_summary.typ`
  (examples). Caveats: Túnel Boquerón has a high-perish site but lands in §4 via its med/remote
  sites (high+remote isn't in the user's rules); bundle map shows ALL candidate labels in its
  extent, not just the 35; no site notes contain "headscarp" yet though the cover note mentions it.
- 2026-07-05 — Packet fixes: cover note corrected to **"head scarp"** (two words — matches the
  actual note text on sites 44/60/86). **Vantor mosaic demoted to last-resort imagery** (cloud
  cover + apparent nighttime collection makes it hard to read): scene picker now sorts vantor
  behind all other scenes; 18 units re-picked — 17 moved to Pelican 0.62m / SkySat 0.78m, only
  **site 61** keeps vantor (sole coverage there). Figures re-rendered; credits refreshed;
  `reports/report.pdf` recompiled (38 pp).
- 2026-07-05 — **Site 94's packet page was a cloud wall**: the geometric picker chose SkySat u0002
  (only footprint fully containing the 1:2000 extent) but that scene is 100% cloud there — the
  picker optimizes coverage+GSD and is blind to cloud. Hand-overrode unit 94 in report_plan.json to
  pelican 150535 + skysat underlay (the validated combo; underlay corner noted "cloud-obscured" in
  the credit) and re-rendered. Reviewed ALL 36 figures via a contact sheet (brightness/stddev
  heuristics were unreliable — grey cloud ≈ dark forest statistically). Remaining imagery-limited
  pages (no better scene exists): Túnel Boquerón (partial cloud), site 60 (haze), site 61
  (vantor-only, dark), site 109 (very dark forest). Flagged to Lorne.
- 2026-07-05 — **KMZ companion for the packet**: `reports/export_kmz.py` (simplekml — the leftover
  notebook dep earns its keep) → `reports/geer_venezuela_candidate_sites.kmz`. All 110 sites,
  foldered to mirror the packet: Priority 1–5 folders (= report sections 2–6) in packet order,
  group sub-folders, points named by site_no, yellow-dot style matching the maps, description
  balloons with the packet-table attributes. Regenerate after site edits: export_site_data.py →
  (plan/figures if geometry changed) → export_kmz.py.
- 2026-07-07 — Lorne added **4 new candidate sites (111–114)** in QGIS (layer now 114 features;
  all med-perishability / remote). **Populated `road_dist_m`** for the 4 = straight-line distance to
  nearest drivable road, EPSG:32619, rounded to 10 m (same method as before), written through the
  QGIS edit session: 111=1570, 112=940, 113=920, 114=570 m. Regenerated `reports/site_data.json`
  (114 sites). Built a **standalone 2-page report for just these 4** (`reports/new_sites.pdf`, from
  new `reports/new_sites.typ` reusing `template.typ`): p1 = cluster 111/112/113 at 1:6000, p2 =
  site 114 at 1:3000. Imagery notes: all 4 sit on a steep interior flank S of the coastal cluster
  where post-event optical is poor — the only scene covering 111–113 is **skysat 0.79 m u0001**,
  whose east flank is deep terrain-shadow (RGB ~27–40, near-black); recovered it with a **0–110
  contrast stretch** on a cloned renderer (112/113 show clear tan debris scars, 111 a fainter one).
  caracas skysat 0.87 m is cloud there; **site 114 uses pelican 0.65 m caracas 145824** (bright,
  full coverage). Locators = Esri hillshade + OSM arterials + candidate dots + red extent box
  (added a `basemap-credit` param to `template.typ`, default `© Google`, passed `© Esri` here).
  Figures rendered headlessly via `QgsMapRendererParallelJob` into `reports/figures/new_*.png`
  (nodata → dark `#1a1a1a` background). Main packet (`report.pdf`)/KMZ not rebuilt — those still
  cover 110 sites; regenerate when 111–114 should join the full deliverable.
- 2026-07-07 — Lorne added **9 more candidate sites (115–123)** (layer now 123 features); computed
  and committed `road_dist_m` (same method): 115=240, 116=410, 117/118=510, 119=1040, 120=960,
  121=900, 122=830, 123=780 m. All covered by one scene, **skysat 0.73 m `20260627_112621_ssc2_u0002`**,
  and here it's **bright** (RGB ~44–114, no cloud/nodata) — just a gentle 0–150 stretch. They form
  two sub-clusters ~850 m apart (NE of and higher than 111–114): **east 115–118** and **west
  119–123**. Extended `reports/new_sites.typ` to **4 pages** (`new_sites.pdf`): +p3 east 115–118 @
  1:6000, +p4 west 119–123 @ 1:6000. 115 is the only high-perishability/populated one (near cleared
  land at the scene edge); nudged the east figure N so 115 doesn't hide under the top-right locator
  inset. Regenerated `site_data.json` (123 sites). Report now covers all 13 new sites (111–123).
- 2026-07-07 — Per Lorne: **labeled `new_sites.pdf` "Supplement 1"** (added a `doc-label` param to
  `template.typ`, shown bold in the header right-block; default `none` so `report.typ` is unaffected)
  and **switched its locator insets to the Google Maps roadmap base** (`lyrs=m` XYZ) to match the
  main report's locators, replacing the interim Esri hillshade — re-rendered all 4 `new_*_loc.png`
  (Google base + candidate dots + red extent box), credit back to `© Google`. `new_sites.typ` now
  curries `site-page.with(doc-label: [Supplement 1], basemap-credit: [© Google])`.
- 2026-07-07 — Per Lorne: (1) **halved the locator candidate-dot size** (2.6 → 1.3 mm) so the dots
  no longer obscure the red zoom box / each other; re-rendered all 4 `new_*_loc.png`. He likes the
  dots on the area map (the original report's locators had none). (2) **Refactored the report Typst
  into stable-template + thin-drafting-file** to stop main/supplement from silently diverging (the
  Esri-vs-Google locator drift). `template.typ` (rarely touched) now also holds `cover-page()` and a
  single `packet(doc-label:, cover:, units:)` entry point. **Both** `report.typ` and `new_sites.typ`
  are now thin drafting files that just set toggles + list pages and call `packet`: cover on/off =
  pass `plan.cover` or `none`; Supplement badge = `doc-label: [Supplement N]` or `none`. Locator
  base defaults to `© Google` in `site-page`, so no per-doc credit override. Both PDFs recompiled
  and verified (main cover intact; Supplement 1 badge + small dots on all 4 pages).
- 2026-07-07 — Per Lorne: **consolidated to a single report drafting file**. Deleted `new_sites.typ`
  and the stale examples file `site_summary.typ` (+ their PDFs); `reports/` now holds only
  `template.typ` (machinery) + `report.typ` (the one drafting file). `report.typ` has a
  **comment/uncomment BUILD CONFIG block** at the top: block (A) = main packet (cover + all
  `report_plan.json` units), block (B) = a supplement (no cover, `doc-label: [Supplement 1]`, the
  111–123 pages hand-listed). Uncomment one, comment the other, then `typst compile report.typ
  <out>.pdf`. Both configs verified → `report.pdf` (main) and `supplement_1.pdf`. Committed default
  is block A. Noted TODO in-file: re-render the main packet's `loc_*.png` with candidate dots to
  match the supplement's region maps (Lorne likes the dots).
- 2026-07-07 — **Pipeline overhaul (claim-audit + Lorne's architecture).** Ran /claim-audit on the
  QGIS→report/KMZ pipeline: the checked-in half (site_data→Typst/KMZ) was already deterministic and
  view-independent, but three steps were un-scripted ad-hoc mcp work — `report_plan.json` (a stale
  frozen "plan"), `road_dist_m`, and the figure/locator/cover rendering. Per Lorne, rebuilt so the
  candidate layer is the ONLY source of truth and the sole per-build choices are mode (full/supplement)
  + a site selection:
  - **Deleted `report_plan.json`.** Sections/groups/order now derive from attributes at build time via
    `reports/_classify.py` (shared by report + KMZ; verified it reproduced the old section assignment
    110/110). Rules: §2 high+populated, §3 med+populated, §4 med+remote, §5 rest (incl. high+remote,
    low+*), §6 = ungrouped AND note=="low confidence" bundle; a group takes its best member's section.
  - **`compute_road_dist.py`** — standalone geopandas/shapely, candidate + drivable-roads geojson →
    `road_dist_m` (EPSG:32619, round 10 m). Reproduces all 123 existing values exactly, idempotent.
  - **`figures/manifest.json`** replaces the plan's render half: per-unit scene/scale/credit/fig/locator,
    keyed by `_classify` unit key (backfilled from the old plan's 36 units + cover). Produced by the
    render step; `build_report.py`/`export_kmz.py` read it.
  - **`build_report.py`** — classify → join manifest → `build/pages.json` → compile `report.typ` (now a
    thin renderer, no config block). `--mode full|supplement --sites all|3,4,94|111-123 [--label]`.
    Unrendered units error with a worklist (the "what needs a figure" signal). Full report rebuilds to
    38 pp identically.
  - **`export_kmz.py`** rewritten to classify from attributes (no plan); covers all 123.
  - **`.claude/skills/geer-report/SKILL.md`** — the one command; orchestrates the python steps + the
    QGIS-mcp render playbook (scale ladder, imagery pick/stretch, Google locator, 1.3 mm dots, exact-scale
    trick, view-independent `setLayers`, manifest schema). Invoke `/geer-report full all` etc.
  - **Only two things still need QGIS-mcp** (by design, per Lorne): the figure/locator/cover PNGs and
    their manifest entries — everything else is a plain `uv run`.
  - **Stale:** `supplement_1.pdf` + `new_*.png` grouped 111–123 by *spatial* judgment; under the
    attribute model they're ungrouped singles (or Lorne sets a `group` attr). Flagged, not deleted —
    the supplement needs a re-render via /geer-report.

## Data provenance & shareability (2026-07-10)

Goal: make the repo shareable — every layer either in git, streamable online, or with a recorded
download link. Built a manifest + tooling and closed two gaps.

- **`data/manifest.yaml`** — source of truth cataloguing all 37 project layers into 3 tiers:
  **12 repo · 9 stream · 16 download** (15 Planet COGs by public Source Coop URL + 1 Vantor mosaic
  marked `fetch: rebuild`, non-redistributable). Shared `sources:` block holds license/attribution.
- **`src/geer_venezuela/manifest.py`** — `check` (parses the .qgz, confirms every project layer is
  catalogued and every repo/download file is on disk), `fetch` (HTTPS-downloads missing download-tier
  COGs into data/basemaps/), `list`. Added `pyyaml` to deps.
- **Layer metadata embedded**: every layer now carries source/download link + license + how-to in its
  QGIS metadata (Layer Properties → Metadata), written from the manifest and saved into the .qgz.
- **Two gitignore bugs fixed**: `imagery_footprints.geojson` (was under gitignored data/basemaps/) and
  `la-guaira_slope.tif` (was under data/terrain/*.tif) are small and layer-critical — now tracked via
  `data/basemaps/*` + `!` exceptions.
- **`DATA.md`** — collaborator guide: the tiers, `fetch`/`check` commands, how to add layers, and the
  **external-drive strategy** (symlink `data/basemaps` → the drive so the .qgz's relative paths stay
  portable; access is by public re-download so no one needs the physical drive).
- **Resolved:** the `landslide_candidates` layer pointed at the pre-rename filename
  `landslide_candidates.csv`; repointed it to `geer_venezuela_candidate_sites.csv` (the name Lorne
  uploaded to the team OneDrive), reads 123 sites, saved. Deleted the stale `site_list.csv` (0–43,
  superseded — flagged stale in this log since the layer→"Candidate sites" rename) and the orphaned
  `landslide_candidates.qmd` metadata sidecar (old filename). One CSV now, the geer_venezuela one.
  `manifest check` is clean.

## Cleanup / slimming for sharing (2026-07-10)

Dropped the route-planning / interpreted-terrain thread and stale scaffolding; kept slope as a base
layer per Lorne.

- **Removed layers + files:** WATCH watch-segments and Steep areas (≥30°) layers pulled from the
  project (saved); deleted `data/routes/la-guaira_watch_{segments.geojson,corridors.csv}` and
  `data/terrain/la-guaira_steep30.geojson`. Kept: Slope, Geology, Arterials, Drivable roads.
- **Trimmed dead code:** removed `watch_segments()` from `roads.py` and `steep_areas()` from
  `terrain.py` (+ their `__init__.py` exports and the now-unused `_UTM`). `fetch_roads`/`fetch_dem`/
  `compute_slope` remain; package still imports clean.
- **Untracked cache:** `cache/` (28 MB regenerable STAC/geology API responses) `git rm --cached` +
  gitignored — was tracked, shouldn't be.
- **Working notes:** `_temp.md` untracked + gitignored (kept on disk). `bare_bones.md` and the
  `docs/` folder (`field_recon_priorities.md`) were deleted by Lorne — recorded the removals and
  scrubbed every reference from README, scripts, and manifest.
- **README** rewritten where it named removed items; the "Field-team deliverable" section now points
  to `reports/` (PDF + KMZ via geer-report) instead of the deleted planning notes.
- `manifest check` clean: 35 layers (10 repo · 9 stream · 16 download).
- *Note:* earlier Phase 2/3 entries above are kept as historical log; they mention the now-removed
  watch/steep products.

## New data: vegetation + 1999 Vargas mosaics (2026-07-15)

Two datasets from `data/temp_to_sort/` sorted into the project.

- **Vegetation formations (national, 2010):** translated the Spanish shapefile
  `101231_Formaciones_vegetales_2010_WGS84` (23 polygons, Huber & Alarcón formations, EPSG:4326)
  to `data/terrain/vegetation_formations_2010.geojson`. Original Spanish `FV_VE` kept intact;
  English added as `veg_en`. Added under **Terrain & Geology**, categorized by `veg_en`, off by
  default. GeoJSON + git-tracked (sits next to the geology layer).
- **1999 Vargas aerial mosaics (post-disaster, flown 21–27 Dec 1999, ~1:15,000):** scanned photo
  mosaics of the Camurí→Caraballeda→Tanaguarena→Macuto coast — none were georeferenced (pixel-space,
  no CRS). Moved all 10 files to `data/basemaps/historical_1999_vargas/` (gitignored, not tracked).
  Georeferenced the two best via QGIS Georeferencer (Lorne placed GCPs against the BEFORE layer),
  then GDAL TPS + cubic warp to EPSG:4326:
  - `Camuri_Chco-Cerro_Grande.jpg` (17 GCPs) → `BEFORE-1999 — camuri-caraballeda · aerial mosaic 15k · 1999-12-27.tif`
  - `Mosvar.tif` (48 GCPs, wide strip) → `BEFORE-1999 — vargas coast · aerial mosaic 15k · 1999-12-27.tif`
  Both ~2.8 m/px, overviews built, added under **Basemaps** (off by default). The `.points` files
  are kept alongside the sources so either warp can be re-run. Remaining 8 files are redundant
  crops/versions (`Mosvargas Camuri-Naiguata.jpg` == `Mosvar2r.jpg`, byte-identical) left un-warped.
  These are a valuable historical BEFORE-analog: they show the 1999 debris fans and channel scour.

## Imagery expansion: Satellogic, Maxar, PlanetScope + border fixes (2026-07-21)

Added three streams of post-event imagery and fixed opaque-border problems on two of them.

- **Satellogic (NASA Earthdata) — streaming.** From the Web Map item `3edc2b4ea24e…` pulled two
  ImageServers (`202611_satellogic` true color, `202611_satellogic_ndvi`). Added under **NASA
  Disasters (Earthdata)** via the `arcgismapserver` provider (EPSG:3857, jpgpng), matching the other
  NASA layers. Partial swaths over the La Guaira/Caracas coast, off by default. Verified live with a
  direct `exportImage` (QGIS render times out on the slow Earthdata TLS — a known quirk, not a fault).

- **Maxar/Vantor WorldView deliveries → clipped visual GeoTIFFs.** 6 unique scenes (25–26 Jun 2026,
  WV-2/WV-3, ~0.46 m) live on the external One Touch drive as raw 8-band/16-bit R#C# tiles. Built a
  VRT per delivery (absolute paths, in `data/basemaps/maxar_external/`), then translated to 8-bit RGB
  (natural color R=band5/G=band3/B=band2) and **clipped to each scene's XML footprint** via
  `gdalwarp -cutline` → JPEG/YCbCr GeoTIFFs with a lossless internal mask (clean transparent border,
  no collar). Output in `data/basemaps/maxar_visual/` (gitignored), ~100 MB–1 GB each, added as
  **AFTER** layers off by default. 5 of 6 done; **puerto-cabello (`S3DS_362958`) still to regenerate**
  from its VRT (first clip came out empty from a bled-JPEG source; needs the drive reconnected).
  Full recipe + the GDAL-codec/PROJ gotcha are in the `maxar-external-drive-imagery` memory.
  Footprint layer: `data/basemaps/maxar_visual/maxar_footprints.geojson` (from the XML corners).

- **PlanetScope post-event time series — on the drive.** 63 scenes (`*_3B_AnalyticMS_SR.tif`, 4-band
  B/G/R/NIR, 16-bit, 3 m, EPSG:32619, LZW + internal overviews) in
  `/Volumes/One Touch/satellite_imagery/post_earthquake`, spanning 15 dates 2026-06-25→07-17. Added
  in place (not copied) under a **"PlanetScope post-event (external)"** group with a per-date
  subgroup, chronologically ordered, off by default. True color R=3/G=2/B=1. Rendering: after testing
  per-scene cumulative cuts (which made water-heavy/hazy scenes look inconsistent), settled on a
  **shared fixed stretch min=200/max=3500 on all RGB bands across all 63** for a consistent look
  (Lorne confirmed). Band 4 is NIR — available for CIR false-color / NDVI-difference work later.

- **1999 BEFORE mosaics — border fix.** An automated edge flood-fill was tried to drop the scanned-
  paper margins but it removed interior content, so it was reverted: both mosaics were **regenerated
  from the original scans + saved `.points` GCPs** (clean, `-dstalpha` for the warp collar only).
  The proper trim is a hand-drawn crop polygon per mosaic → `gdalwarp -cutline`; step-by-step
  instructions saved in `docs/trimming-1999-mosaics.md` (includes the rebuild-from-points recipe).
  Lorne to draw the polygons when ready.

- **GDAL note:** the `gdal_translate` on PATH is GDAL 3.3 (Postgres.app) with no JPEG codec — use the
  QGIS-bundled GDAL 3.12 at `/Applications/QGIS-LTR.app/Contents/MacOS/` with `GDAL_DATA`/`PROJ_LIB`
  pointing under `Contents/Resources/qgis/` (the `/qgis/` segment is required or PROJ drops the CRS).

## GeoSyntec geomorphic aerial interpretation (2026-07-21)

Colleague shared two shapefiles via OneDrive (`GeomorphAerials_07192026`, `GeomorphAerials_07202026`).
Checked: the 07-20 file is a clean **superset** of 07-19 (all 424 of the 19th's IDs present, plus 92
new = 516 features; identical schema/extent/CRS). So only the newer 07-20 was imported.

Converted the 07-20 shapefile to `data/geosyntec/geosyntec_geomorph_aerials_20260720.geojson`
(EPSG:4326, git-tracked). Added under a new **GeoSyntec** group, categorized by `Type`
(452 Landslide, 41 Liquefaction, 16 Ground Rupture, 7 Ground Settlement), off by default.
Attributes include Confidence, subtype (LS/LQ/GR), Impact, Source, Comments. Manifest updated
(new `geosyntec` source; 110 layers, audit clean apart from the stray Avila KML).

## Slope & aspect characterization + Avila line inventory (2026-07-21)

Characterized slope magnitude and orientation (aspect) for the earthquake landslide datasets from
the 30 m Copernicus DEM (`data/terrain/la-guaira_dem.tif`), reprojected to UTM 19N so slope is
computed in meters. Aspect uses a **circular mean** (vector average) throughout, so a north-facing
feature never wrongly averages to south.

- **Candidate points (123):** sampled slope/aspect at each point; added `slope_deg`, `aspect_deg`,
  `aspect_dir` to the Candidate sites layer. Median slope 27.8°; strong N/NE/NW aspect bias.
- **GeoSyntec polygons (516):** zonal stats (all_touched, so sub-cell polygons still get values;
  0 needed centroid fallback). Added `slope_mean/min/max`, `aspect_deg`, `aspect_R`, `aspect_dir`,
  `n_cells`. Types separate as expected: Landslide 33.8° mean, Liquefaction 2.2°, Settlement 3.1°,
  Ground Rupture 5.9° — validates the mapping. 452 landslides face dominantly NE.
- **Ávila line inventory (640 lines):** the actual landslide-line dataset (was loaded from
  `~/Downloads/VenLS_AvilaDRAFT_15July2026.kml`). Imported to
  `data/usgs_avila/venls_avila_inventory_line_20260715.geojson` (EPSG:4326, git-tracked); layer
  re-pointed at the repo file under the **USGS** group. Slope/aspect sampled every ~15 m along each
  line: `slope_mean/max`, `aspect_deg`, `aspect_R`, `length_m`, `aspect_dir`. Total mapped length
  52.4 km, median slope 37.1°. Note: the earlier `USGS rapid assessment` polygon layer is a uniform
  ~2.45 km assessment grid (335 identical cells rated minor/localized/major), NOT landslide shapes —
  not suitable for a slope/aspect rose.

**Consistent finding across all three datasets:** landslides concentrate on **NE-facing, steep
(≥40–50°) slopes** — the seaward face of the coastal range. Area/length weighting strengthens the NE
signal further (NE = 37% of GeoSyntec landslide count but 44% of area; 35% of Ávila line count but
41% of length).

- **Notebooks** (`notebooks/`, Jupyter; env has geopandas+matplotlib+rasterio): stacked slope-roses
  (aspect × count/area/length × slope class) + companion plots.
  - `candidate_slope_aspect.ipynb`
  - `geosyntec_slope_aspect.ipynb` (landslide-only; count + area roses)
  - `avila_lines_slope_aspect.ipynb` (count + length roses)
- Manifest updated (`geosyntec`, `avila_inventory` sources; 111 layers, audit clean — the stray
  Downloads KML is now a tracked repo layer).

## Route-map report (field trips)

New report type alongside the candidate-site packet: **one page per field-trip route**
(`reports/routes/`), for the 6 planned trips (R1–R5, R5alt). Parallel pipeline, separate from
the site report so neither touches the other:

- `build_route_data.py` → `route_data.json`: per-route ordered POI list (site→route mapping
  transcribed from `_temp.md` as `ROUTE_POIS`) joined to `trip_sites.geojson` attributes
  (coords, setting, slope, aspect).
- `template_routes.typ` (imports the shared `../template.typ` knobs/helpers) + thin
  `report_routes.typ`; `build_route_report.py` joins `route_data.json` to
  `figures/manifest.json` → `route_pages.json` → `typst compile --root reports` (root must be
  `reports/` so the cross-dir import + `site_data.json` both resolve).
- Figures rendered from QGIS: route line (blue) + that route's POIs (yellow numbered dots) over
  **Google roadmap**, with the start/end **point labels removed** (start = green triangle, end =
  red triangle, unlabeled — the start → end text lives in the page header instead). Locator inset,
  scale bar, north arrow as on the site pages. Loop routes (R5/R5alt) rendered at 1:60000 to fit
  the airport→south loop; R1 1:50000, R2/R4 1:40000, R3 1:25000.
- Each page carries a POI table (site · coords link · setting · slope · aspect).

Output: `reports/routes/report_routes.pdf` (6 pages).

## Working draft §6.2: GEER-style rewording, Intro + Background (2026-07-24)

Reworked `06_Landslides/working_draft.md` Introduction and Background against the wording style of
three reference GEER reports (2018 Hokkaido Ver.1, GEER-082 Türkiye 2023, GEER-ATC Ecuador 2016;
style evidence pulled per-report: inventory-led openings, past-passive observations, "appeared
to"-class hedges on interpretation but not measurements, present tense for standing geology):

- **Introduction**: count/area moved to the opening paragraph (Hokkaido pattern); failure-character
  sentence now its own paragraph; preliminary-inventory caveat reordered (topic sentence → methods →
  limitations → how to read the numbers). Still open: XX count/area, partner attribution, imagery
  table (Patricia), optional event magnitudes in sentence 1.
- **Background**: placeholders resolved with numbers from `lit_review_1999.md` / `geology_note.md`
  (911 mm storm, ~24 catchments / 50 km coast, 100,000 m³/km² yield, ~1.25 M m³ Caraballeda fan,
  15,000–30,000 deaths; San Julián schist/gneiss, 0.5–2 m regolith, 30–60° slopes). TODO comment in
  draft: confirm López et al. yield wording + year.
- **Background-rate analog corrected then dropped**: Lorne corrected the Puerto Rico figure
  (0.8–2.6 slides/km²/decade, Larsen & Torres-Sánchez 1998 — not the 0.011 %/yr turnover
  paraphrase), then flagged the lithologic mismatch; verified from the paper that its three study
  areas have **no metamorphic bedrock**. Lit search (Serra do Mar; metamorphic belts; lithology-
  stratified compilations) → new note `06_Landslides/background_rate_note.md`. Key: no chronic rate
  published for Serra do Mar (the closest gneiss-escarpment analog) or the region; lithology is a
  second-order control. **Report handles background qualitatively** (pre-event slides screened out
  as "tricky true negatives" during mapping; coseismic observably more extensive); the rate
  compilation is reserved for a future paper. `lit_review_1999.md` §4 updated accordingly.

Next: Trends (subsection names appear swapped vs. their content/figures), Compounding hazard,
Site observations. Opportunities section was completed in a prior session.

## Literature review audit + consolidation (2026-07-24)

Lorne flagged unreliable attributions in the lit notes (claims cited to Larsen et al. 2001 that
aren't in the paper). Ran a claim-by-claim provenance audit: read Larsen et al. 2001 (FISC), USGS
OFR 01-0144, Map I-2772 pamphlet, FS-103-01, and López & Courtel 2008 in full; re-verified
Larsen & Torres-Sánchez 1998, Larsen 2012 (PP 1789-F), and Broeckx 2019 from on-disk extracts.

- **New single document `06_Landslides/lit_review.md`** replaces `geology_note.md`,
  `lit_review_1999.md`, `background_rate_note.md` (deleted). Every citation carries a URL and a
  read-status code (FULL / FULL-A / PARTIAL / ABSTRACT); read sources are quoted verbatim; a
  25-row claims-audit table records verdicts and fixes.
- **Key verdicts**: lithology (Tacagua/San Julián/Peña de Mora), soil 0.5–3 m, failure depth
  0.5–2 m, slopes 30–>60° are all OFR 01-0144, not Larsen 2001 or FS-103 (recited). "~24 streams"
  is López & Courtel 2008. Two figures were in NO source read and were removed from the draft:
  "sediment yield 100,000 m³/km²" and "~200 km² contributing area" (also "uplift 2–5 mm/yr").
  Event-total deposition is 20 M m³ (López et al. 2000, secondhand via I-2772). Sources conflict
  on: death toll (15–30k vs ~19k), Caraballeda fan volume (1.25 vs 1.8–1.9 vs ~2 M m³), coast
  length (50/40/20 km) — the review records all; the draft reports ranges.
- Source PDFs/extracted texts archived in `data/references/lit_audit_20260724/` (gitignore
  status: data/basemaps is ignored; check whether to track these).
- Working draft Background rewritten against verified quotes only.

## Fig. 6.2 aspect rose script (2026-07-24)

`scripts/fig6_2_aspect_rose.py` (run: `uv run python scripts/fig6_2_aspect_rose.py`) — count-based
aspect rose combining the GeoSyntec landslide polygons (precomputed `aspect_deg`) with the
GEER-mapped lines from `geer_mapping.gpkg` (aspect computed from DEM: warp to UTM 19N, Horn
gradient, circular mean of ~15 m samples along each line, slope <2° excluded). Each feature
counts 1 (mixed geometry types). 16 sectors, notebook-consistent binning; CVD-validated
blue/orange stacked bars; writes `06_Landslides/fig6_2_rose_count.png` (300 dpi) + console table.
The mapped lines lie WEST of the la-guaira DEM, so fetched `data/terrain/geer_mapping_dem.tif`
(Copernicus GLO-30 via `geer_venezuela.terrain.fetch_dem`, lines extent + 0.02° pad); the script
globs `data/terrain/*_dem.tif` and samples each line from whichever DEM covers it — new mapping
areas just need one fetch_dem call. Result: 452 polygons + 150 lines, both inventories peak
NE/ENE; the lines skew farther east (E sector: 30 of 63 total).

## GeoSyntec layer cleanup — analysis attrs removed (2026-07-24)

Lorne flagged that repo scripts had earlier written derived attributes into the GeoSyntec source
layer, which he did not want. Removed `slope_mean, slope_min, slope_max, aspect_deg, aspect_R,
n_cells, aspect_dir` from `data/geosyntec/geosyntec_geomorph_aerials_20260720.geojson` (back to
the original 15-column delivery schema, 516 features). Followed the CLAUDE.md open-file
procedure: saved style QML → removed layer from live QGIS → edited on disk → re-added into the
GeoSyntec group → re-applied style. Project NOT saved (Lorne's call in QGIS).
`scripts/fig6_2_aspect_rose.py` reworked accordingly: no attributes expected on either input —
polygon aspect is now computed at run time (circular mean of DEM aspect over cells inside each
polygon; representative point for tiny polygons), same DEM/gradient/slope-filter method as the
lines. All 452 polygons + 150 lines resolve; counts near-identical (NE peak 101 vs 105).
**Rule going forward: analysis products don't get written into source data layers — compute at
run time or write to separate files.**

- Fig. 6.2 script restyled per Lorne: Arial font; petals now stacked by max-slope class
  (notebook SLOPE_BINS 0/20/30/40/50/90, ColorBrewer Blues light→dark) instead of by dataset;
  slope computed per feature from the DEMs alongside aspect (max over covered cells/samples).
  Inventories pooled by count (452 polygons + 150 lines; dataset split still printed to console).

## USGS Ground Failure landslide models added (2026-07-24)

Downloaded the ground-failure product rasters for event us6000t7zp (M 7.5, 20 km ESE of Yumare,
GF version 12 of 2026-07-13, ShakeMap v12) via ComCat into `data/usgs/ground_failure/`:
`jessee_2018_model.tif` (preferred; max prob 0.21, alert red), `godt_2008_model.tif`,
`nowicki_2014_global_model.tif`, plus `info.json` (alerts, aggregate hazard 46 km², pop exposure
~13,000, model refs). Liquefaction models (zhu_2015, zhu_2017_general) NOT downloaded — available
in the same product if wanted. Added all three to the QGIS **USGS** group as
"GF landslide probability — <model> (USGS…)", styled singleband pseudocolor (USGS-style
yellow→red, <2% transparent, 75% opacity, classification 0–0.4). Project not saved (Lorne's
call). NB for §6.2 comparison: info.json flags `point_source: true` + `rupture_warning: true` —
the GF run used a point-source approximation for this M 7.5 event.

## Vantor Open Data inventory + download script (2026-07-24)

Compared the project's holdings against the Vantor open-data STAC collection
(`vantor-opendata.s3.amazonaws.com/events/Venezuela-Earthquake-Jun-2026/collection.json`;
Maxar Open Data IS now activated for this event — earlier PROGRESS notes said it wasn't).
Collection: 48 unique items (49 links, one duplicate), 10 pre-event Nov 2025–May 2026 +
38 post-event Jun 25–30, ~349 GB of visual COGs. File-level overlap with the project:
(1) the two "wv2" 2026-06-25 21:29 Maxar deliveries in `maxar_visual/` are the exact same
collects as open-data items B16000110179D310/D410 (times + off-nadir match to the second —
NB the open data labels them **LG06/Legion-6, not WV-2**; local file/layer names likely
mislabeled); (2) `vantor_legion_20260625_mosaic.tif` derives from the five Jun-25 Legion
post scenes. The other five Maxar deliveries (la-guaira-west, puerto-cabello ×2,
valencia-west ×2) are NOT in the collection. Remaining 43 scenes we don't have = 327 GB
(96 GB pre / 231 GB post; 2.1–51 GB each — the 51 GB one is the WV03 2026-05-31 pre-event
strip). Too big for the repo/internal disk (146 GB free) → destination is the One Touch
drive (2.9 TB free). Wrote `scripts/download_vantor_opendata.sh` (resumable curl loop,
size-verified, STAC JSON sidecars, pre_event/post_event subfolders, default dest
`/Volumes/One Touch/satellite_imagery/vantor_open_data`; `INCLUDE_MOSAIC_SCENES=1` adds
the three Jun-25 LG01 full-res scenes, ~8 GB). Not yet run — Lorne to launch.

## §6.2 Trends section rewrite around aspect rose (2026-07-24)

Rewrote the Trends section of `06_Landslides/working_draft.md`: dropped the
Watersheds/Directionality subsections in favor of one narrative that (1) describes the
northeastward aspect trend using `fig6_2_rose_count.png` (ran
`scripts/fig6_2_aspect_rose.py` for the numbers: 602 pooled features = 452 GeoSyntec
polygons + 150 GEER lines; 391/602 ≈ 65% face N–E, NE+ENE ≈ 30%, <10% face south,
dominant petals mostly 40°+ max slope), (2) attributes it to steep north-facing coastal
terrain plus westward fault displacement destabilizing east-facing slopes (with an honest
caveat that the inventory isn't normalized by terrain aspect), and (3) closes on the
north/south drainage-divide split (coastal fans vs. Caracas basin margin) to tee up the
compounding-hazard section. Fig. 6.3 watershed figure and the USGS Ground Failure
qualitative-comparison caveat retained.

## Vantor Open Data streaming: footprints + first vsicurl scene (2026-07-24)

Verified the bucket's files are true COGs (LZW, 512-px tiles, full overview pyramids +
mask bands) → stream well via `/vsicurl/` with no download. New
`scripts/vantor_opendata_footprints.py` (stdlib + certifi for the macOS framework-Python
TLS gotcha; run `uv run python scripts/vantor_opendata_footprints.py`) fetches the STAC
collection and writes `data/basemaps/vantor_opendata_footprints.geojson` — 48 scene
polygons with datetime/era (Temporal Controller compatible), sensor/vehicle, gsd, cloud,
off-nadir, size_gb, holding (delivered-scene / mosaic-source / stream-only) and a
ready-to-paste `vsicurl` URI per scene. Added to QGIS at root beside "Imagery footprints
(toggle)" as **Vantor Open Data footprints (toggle)**: era-categorized outlines (after
solid orange, before dashed blue), map tips show id/label/cc/size/holding. Also added the
first streamed layer to the AFTER group: **AFTER — maracay · worldview-3 0.32m ·
20260626_151035 (Vantor stream)** (B040001100074D10, 0% cloud; gdal provider over
vsicurl; off-screen render test confirmed tiles arrive). Recipe for more scenes: copy the
footprint feature's `vsicurl` attribute → Add Raster Layer (or ask Claude), name per the
AFTER convention with "(Vantor stream)" suffix. Project NOT saved (Lorne's call).

## Ground Failure: trimmed to Nowicki Jessee 2018, both mainshocks (2026-07-24)

Per Lorne: Godt 2008 and Nowicki 2014 not needed — layers removed from the USGS group and
their rasters (+ QGIS aux.xml sidecars) deleted from `data/usgs/ground_failure/`. Remaining
layer relabeled **GF landslide probability — Nowicki Jessee 2018 — M 7.5 Yumare (USGS
us6000t7zp)**. Added the same model for the second mainshock: **… — M 7.2 San Felipe (USGS
us6000t7zc)** (GF version 7; alert orange, max prob 0.12, aggregate hazard 11 km², pop
exposure ~1,700; extent spans both events' region). Files:
`jessee_2018_model_us6000t7zc.tif` + `info_us6000t7zc.json` (event-ID suffix; the
unsuffixed pair remains the M 7.5 us6000t7zp product). Style cloned from the 7.5 layer
(USGS yellow→red pseudocolor, 75% opacity), inserted directly below it. NB: the 7.2 GF run
also flags `point_source: true` — check info_us6000t7zc.json before quoting numbers.
Project NOT saved (Lorne's call).

## Geology layer expanded to full study region (2026-07-24)

Per Lorne: geology coverage widened from the La Guaira box (32 units,
-67.12..-66.72 / 10.40..10.63) to the whole study region **LL 10.0/-69.3 → UR 10.7/-66.4**
(Puerto Cabello through La Guaira). New `scripts/fetch_geology.py` (bounds constant +
usage note incl. the SSL_CERT_FILE workaround) wraps `geer_venezuela.fetch_geology`; wrote
`data/terrain/geology.geojson` — **426 units** at Macrostrat zoom 11 (same USGS 1:750k
source map). QGIS: old layer removed first (file-cache gotcha), new layer added in its
place ("Terrain & Geology" group, index 1, visibility kept OFF as before), style preserved
via saved `data/terrain/geology.qml` (single symbol, fill data-defined
`set_color_part(coalesce("color",'#cccccc'),'alpha',89)`). Superseded
`la-guaira_geology.geojson` deleted (regenerable from the script by narrowing BOUNDS).
Project NOT saved (Lorne's call).

## Notebook: GF-model aspect rose, M 7.5 event (2026-07-24)

New `notebooks/jessee75_prob_aspect.ipynb` — aspect rose for the Nowicki Jessee 2018 M 7.5
Yumare model (companion to the candidate/GeoSyntec/Avila slope-aspect notebooks, but per
Lorne stacked by **modeled probability class** instead of slope class; probability bins
0.002/0.005/0.01/0.02/0.05+, yellow→red). Params up top: `WEST_CUTOFF` (default −67.8;
None = full footprint) and `PROB_THRESHOLD` (0.002). Pipeline mirrors
fig6_2/`geer_venezuela`: keep model cells ≥ threshold & east of cutoff → fetch GLO-30 for
their bounds (cache `data/terrain/dem_cache_<bounds>.tif`, gitignored, ~46 MB for the
default cutoff) → UTM 19N Horn gradient → sample aspect/slope at cell centers, drop
slope < 2°. Headline rose = summed probability per 16 sectors (saved
`jessee75_rose_prob.png`); companions: cell-count rose (`jessee75_rose_count.png`) +
8-direction summary table. Run at defaults: 55,958 cells, Σp ≈ 615; **N-facing peak**
(N sector Σp 135 vs SE/S minima ~42–45) — NB the mapped inventories peak NE, worth a
sentence in §6.2. Executed headless via `uv run jupyter nbconvert --execute`.

## All 48 Vantor Open Data scenes added as streamed layers (2026-07-24)

Per Lorne: every scene in the collection now streams in QGIS via `/vsicurl` (gdal
provider), same recipe as the maracay demo. 38 post-event → flat **AFTER — post-event
imagery** group (59 layers total now); 10 pre-event → new **BEFORE — Vantor pre-event
(stream)** group inserted above BEFORE-1999. Names:
`<ERA> — <nearest-town> · <sensor> <pan_gsd>m · <YYYYMMDD_HHMMSS> (Vantor stream)`,
town from footprint-centroid nearest-match (gazetteer of 15 regional towns; NB the long
N–S coastal strips centroid-match to "caracas" even when they cover the La Guaira coast —
incl. the two 20260625_2129xx legion scenes whose local Maxar-delivered clips are named
la-guaira; rename if that grates). All added **visibility OFF** (48 remote strips
rendering at once would hammer the network) — the earlier maracay demo stays ON as
before; chronological order within each group; skip-if-name-exists guard makes the add
idempotent (one MCP timeout double-ran a batch harmlessly). All 48 layers valid, CRS
still EPSG:4326. Project NOT saved (Lorne's call).

## MGRS inspection grid: 10 km + nested 1 km curtain (2026-07-25)

Per Lorne: systematic-inspection grid on the standard MGRS/UTM 19N kilometer grid
(REGVEN-compatible; study region sits wholly in zone 19N band P, 100-km squares
19PDM–19PGM). New `scripts/build_inspection_grid.py` (uv run; MGRS lettering computed and
verified against known references) writes `data/grids/inspection_grid.gpkg`:
**grid_10km** (297 cells, ids like `19PGM45`) + **grid_1km** (29,700 children, ids like
`19PGM4256`, `parent_id` link), both with `show` 0/1 (default 0). QGIS: new group
**Inspection grid (toggle)** (added OFF) above the imagery groups / below the vector
overlays — cells with show=0 render as a white ~60–63% curtain hiding imagery beneath;
show=1 renders outline-only (imagery visible). Labels: short MGRS suffix, scale-limited
(10 km ≤1:1.5M, 1 km ≤1:60k). **Click-to-toggle**: each layer carries a Python QgsAction
("Toggle cell") — pick it under the Run Feature Action tool ▾ and click cells on canvas;
edits commit straight to the gpkg, so open/closed state persists across sessions and
doubles as the inspected-cells record. Round-trip toggle verified; styles+action saved
into the gpkg as default styles (survive re-add). Two-tier use: open a 10 km cell to
reveal the 1 km curtain, then open 1 km cells; whole tiers toggle via layer checkboxes.
Re-running the build script resets inspection state (and needs layers removed first —
file-cache gotcha). Project NOT saved (Lorne's call).

## la-guaira-west blackout diagnosed + OAM add + imagery-zone reorg scripts (2026-07-27)

- **OAM caracas-corridor COG added.** `tiles.openaerialmap.org` is 503 (whole host down; API up),
  but the source GeoTIFF survives on S3 (`oin-hotosm-temp…/6a437f8fa8d2fe29ac06614d/0/…614e.tif`,
  240 MB COG, 0.86 m, EPSG:4326, 34×54 km spanning caracas/catia-la-mar/la-guaira, 49/125 candidate
  sites). Added from `~/Downloads/6a437f8fa8d2fe29ac06614e.tif` (**pending move into
  `data/basemaps/`**). Heavy cloud over the interior ranges; **acquisition date UNVERIFIED** — S3
  upload 2026-06-30 is not capture date; no OAM API record for this id.
- **la-guaira-west (Maxar S2AS_366001) black rectangle: root cause found.** The 26.5 × 6.6 km
  opaque box (UTM 680598–707063 E / 1152455–1159053 N; RGB≈1 fill) is **4 missing source tiles
  R2C04–R2C07** (of a 3×10 grid): the Jul-15 VRT references only 26/30 tiles, and `gdalbuildvrt`
  skips unreadable inputs silently — same failure family as the puerto-cabello "bled-JPEG" scene.
  The local tif is a faithful render of the holey VRT; nothing to recover locally. Not in Vantor
  open data (the 14:20:38 collect is absent; delivery is non-redistributable). Impact low: 0
  candidate/geer_mapping sites in the gap; Satellogic 100%/OAM 77%/catia-la-mar WV-2 77% cover it.
  → **`scripts/check_maxar_delivery_tiles.sh`** (new): run with the One Touch drive mounted;
  validates all 30 tiles (exists/opens/decodes via QGIS-bundled GDAL), tells rebuild-vs-reorder.
  NB the working GDAL 3.12 lives in **QGIS.app** (`Contents/MacOS/`), not QGIS-LTR.app.
- **Imagery layer reorg designed (with Lorne), scripts staged but NOT yet applied:**
  (1) **date-first names** — `AFTER — MM-DD · <gsd>m <sensor> · <loc> · <id>` (BEFORE keeps
  YYYY-MM-DD), so alpha sort = chronological → `scripts/rename_imagery_layers.py` (DRY_RUN
  default; 69 renames verified; OAM layer skipped pending a real date in `DATE_OVERRIDES`).
  (2) **zone index groups** — `scripts/build_imagery_zones.py` (DRY_RUN default) builds
  "ZONES — AFTER imagery (index)": 0.25° cells (fixed A1 anchor -69.0/11.5, codes stable),
  each holding **pointer nodes** to intersecting AFTER layers (verified: QGIS renders a layer
  when ANY checked reference is under a checked group; pointer removal via API leaves the layer
  intact) + labeled `data/derived/imagery_zones.geojson` canvas index. Dry run: 60 layers →
  42 cells / 240 pointers (0.5° would give ~15). **Footgun:** right-click "Remove Layer" on a
  pointer removes the layer everywhere — rebuild via script only. Built-in "Filter Legend by
  Map Content" was ruled out first (vector-only; QGIS #14194/#38402/#45453).

## Imagery reorg applied (after a recovered layer-wipe) (2026-07-27, evening)

First application attempt went sideways: the zone build crashed on `renderer()` (None on a
geometry-less layer), and during the confusion **70 layers (all AFTER + BEFORE-Vantor) were
removed from the project registry** — pattern consistent with a GUI *Remove Group/Layer* on
pointer-bearing groups (GUI removal deletes the layers everywhere; script-side node ops were
re-verified registry-safe). No data lost: the 15:33 on-disk save predated everything; QGIS
restart + reload recovered all layers. Scripts hardened (clone-based re-sort keeps ≥1 tree ref
per layer at all times; zone build aborts on an empty AFTER group; registry-count asserts; explicit
`QgsSingleSymbolRenderer`). Then the full pipeline ran clean: OAM layer re-added, **69 layers
renamed** to date-first (OAM skipped pending verified acquisition date → `DATE_OVERRIDES`),
groups re-sorted chronologically, **42 zone groups / 240 pointers** built + labeled
`data/derived/imagery_zones.geojson` index (render-verified). Registry 184. Project NOT saved —
Lorne's call. **Rule: never right-click-remove a pointer or zone group — rebuild via
`scripts/build_imagery_zones.py`.**

- **Naming/grid revision (same evening, per Lorne):** era prefixes dropped from imagery layer
  names (`06-27 · 0.65m pelican · caracas · id` — group/zone names carry AFTER/BEFORE; BEFORE
  layers keep full YYYY-MM-DD). Zone codes flipped to letter=row (A north), number=column (1 west),
  anchor NW -69.0/11.0 → groups list alphabetically A1…E7 matching the map. Both scripts updated
  (rename now normalizes from any earlier name generation), rebuilt clean: 42 cells / 240 pointers,
  registry 184. CLAUDE.md conventions updated (era-prefix rule retired). Project NOT saved.

## C7 public-source review + OAM date fix + 2 new NASA layers (2026-07-27, late)

Reviewed all public manifest sources for new imagery in grid cell C7 (-67.5→-67.25, 10.25→10.5,
maracay): **nothing new** — Vantor open-data collection unchanged (48 items; the 7 intersecting C7
are all already streamed), NASA `202611_SkySat` bbox-overlaps but its catalog has 0 footprints in
the cell, Esri Wayback's new 2026-06-30 release redirects all C7 tiles to the 2026-02-26 release
(no post-event basemap there), OAM's 7 hits are the same Vantor collects (as ready-made S3 COGs).
Side findings acted on: (1) the OAM caracas-corridor COG identified via OAM API as Vantor collect
**B0300011000DFB10, WV-2, 2026-06-27** — DATE_OVERRIDES set, renamed to
`06-27 · 0.86m OAM · caracas-corridor · …`, zones rebuilt (same 42/240); it duplicates the
`catia-la-mar · 151506` stream as a local COG. (2) NASA event folder grew 10→15 services; added the
two <2 m color ones per Lorne — **202611_SkySat** (0.5 m, 4-band) and **202611_VANTOR_CARACAS**
(0.47 m, raw 8-band U16, server-rendered RGB) — to the NASA group, off; skipped Black Marble HD
pair (12 m/464 m). Registry 186. Project NOT saved.

- **NASA optical imagery folded into the AFTER group (same evening, per Lorne):** the split
  bugged him (rightly — it recreated the two-groups problem and hid layers from the zone index).
  New rule: **AFTER group = all post-event optical imagery regardless of host; NASA group =
  analysis products + coarse reference** (heatmaps, InSAR, NDVI, damage, S2/Landsat, Black Marble).
  Moved 3: `06-26 · 0.50m skysat · aoi-coast · mosaic (NASA stream)`, `06-26 · 0.5-1m satellogic ·
  aoi-coast · mosaic (NASA stream)`, and `06-25 · 0.47m wv-2 · caracas · 212947 (NASA stream)` —
  the last identified via its raster catalog as collect S2AS 200013362935 = a THIRD copy of the
  212947 collect (also local Maxar clip + open-data stream). Zones rebuilt: 63 layers / 300
  pointers; `place_of` now deprioritizes generic wide-footprint names (aoi-coast, caracas-corridor)
  so sparse cells keep real place labels. NB zone membership is bbox-based, so the sparse SkySat
  mosaic advertises in cells where it has no footprints (e.g. C7). NASA group down to 9 (products
  only). Registry 186. Project NOT saved.

- **Zone rebuilds are now position-preserving (per Lorne):** `build_imagery_zones.py` re-inserts
  the ZONES group and the ZONE index layer at their current parent/position (and keeps the index
  layer's checkbox state) instead of forcing top-of-tree; only a first-ever build defaults to top.
  Verified: group at position 14 and index layer at root[0] both survive a rebuild. NB the old
  "Imagery footprints (toggle)" GROUP no longer exists — a layer by that name sits at root — so the
  script no longer targets it.

## la-guaira-west blackout FIXED — tiles recovered from twin delivery zip (2026-07-28)

`scripts/check_maxar_delivery_tiles.sh` (drive mounted) settled it: R2C04–07 are **absent from the
extracted delivery AND from both 366001 zips** — but present in the twin re-delivery zip
`7013438268042418355.zip` (delivery 200013362902, same 14:20:38 collect; each delivery is partial
in a complementary way). Recovery: extracted the 4 tiles (16 GB) to
`satellite_imagery/recovered_142038_R2C04-07/` (vendor folders untouched), rebuilt the VRT from all
30 tiles (old VRT kept as `.pre-recovery`; NB the VRT now references the recovered folder too),
re-ran translate (recomputed mean±2σ stretch: 1–6438/1–6164/1–5563) → warp cutline → JPEG +
internal mask + overviews. Probe of the formerly-black window: mean RGB ≈ 124/129/112 (was constant
1). Layer swapped in QGIS per the file-cache gotcha (remove → replace file → re-add), zones rebuilt
(63/300 unchanged). Holey original kept as `…tif.holey.bak` (1 GB, deletable). Render-verified: gap
filled, no tile seam; tone slightly darker than before (new stretch), collar now transparent.
**New GDAL gotcha:** GDAL 3.12 CLI utilities infer the output driver from the file extension and
`gdalwarp` **exits 1 silently** for unknown extensions like `.tif.new` — always pass `-of GTiff`.
Also: zsh does NOT word-split unquoted vars (use `${=VAR}`) — bit the tile-script args twice.
Puerto-cabello (S3DS_362958) regeneration still pending — likely the same zip-recovery pattern.
Project NOT saved.

## 2026-07-28 — Wayback zoom-error fix

The BEFORE — Esri Wayback 2026-05-28 layer spammed `GDALWMS: Unable to download block` warnings
when zoomed past ~1:2,000: its TMS config requested tiles to `<TileLevel>19</TileLevel>`, but the
2026-05-28 Wayback cache (version 10842) tops out at level 18 over the AOI — level-19 requests
return a hard 404 HTML page (verified with curl; levels 17–18 redirect fine to canonical version
49999). Fixed in place via `setDataSource` (no remove/re-add needed — source string change, not a
file-cache case): TileLevel 19→18 so GDAL upsamples level-18 tiles at closer zooms, plus
`<ZeroBlockHttpCodes>404</ZeroBlockHttpCodes>` so any residual missing tile renders empty instead
of erroring. Layer kept its tree position/style. Project saved.

## GF layer style: QML files, blue-purple no-fill tint (2026-07-29)

To match a collaborator's map (semi-transparent ramp with a blue-purple wash where the model
shows ~zero probability), added `qgis/styles/` with two loadable QMLs for both Nowicki Jessee
layers (Lorne loads them via Properties → Symbology → Style → Load Style; no live restyling):
`gf_landslide_probability_usgs_bluefill.qml` — the original default style recovered from the
saved project's San Felipe layer (yellow→red #ffffb2/#fecc5c/#fd8d3c/#f03b20/#bd0026 at
2/5/10/20/40%, 75% opacity, classification 0–0.4) with the transparent <2% band replaced by a
flat #7472b8 blue-purple; and `gf_landslide_probability_spectral.qml` — an earlier
Spectral-reversed attempt (breaks packed 0.002–0.21, 55% opacity), kept for comparison. NB the
Yumare layer's in-project style had been overwritten manually; the San Felipe layer was the
intact reference.

## GF ramp matched to collaborator's ArcGIS display (2026-07-29)

Iteratively tuned `qgis/styles/gf_landslide_probability_hybrid.qml` against the collaborator's
slide (landslide_photo_gis_matching.pptx, slide 7; caption on slide 6 confirms "blue = less
susceptible, red = more"): flat steel-blue #6285c4 below 0.5%, green #66bd63→#a6d96a to 2.5%,
yellow #ffe14d at 4%, orange #fdae61 at 7%, deep orange #f46d43 at 12%, red #d73027 at 18%,
dark red #a50026 at 0.21 cap; interpolated, 60% opacity. Applied via apply_style_qml to BOTH
Nowicki Jessee layers (Lorne's go-ahead; earlier no-restyling stance lifted for this task).
Tuning loop used macOS screencapture (VS Code granted Screen Recording) because
get_canvas_screenshot/render_map time out — plugin 0.7.1 vs server 0.8.1 mismatch, upgrade
pending. For comparison, temporarily toggled OFF: OpenStreetMap basemap (it sits ABOVE the
hillshade and hides it) and the San Felipe GF layer (double-tint); TOPO Esri World Hillshade
left on. Canvas left on the La Guaira strip. Project NOT saved. Superseded experiment QMLs
kept in qgis/styles/ (spectral, usgs_bluefill).

## Zone visibility script (2026-07-29)

C7/C8 looked emptier than their zone lists promise because `build_imagery_zones.py` assigns
cells by transformed *bounding box* — rotated coastal strips (choroni / catia-la-mar /
la-guaira-west) carry nodata collars whose bboxes reach the inland row without real pixels.
Added `scripts/turn_on_zone_layers.py` (run via exec() in the QGIS console, same pattern as
the zones builder): checks on the ZONES master group, the cell subgroups in its `CELLS` set
(currently B7/B8/C7/C8), and every pointer whose layer streams or has its file on disk;
pointers to missing sources (unmounted Maxar drive) are left off and reported. Never unchecks;
does not save. Lorne cancelled live execute_code runs — mutations go through user-run scripts.

## Crash diagnosis + safe launcher (2026-07-29)

Project load hung minutes, then segfaulted on reopen. Crash report showed (1) load blocked in
QgsProject::preloadProviders with GDAL worker threads stuck in /vsicurl Stat calls —
GDALFindAssociatedFile probing the vantor-opendata S3 bucket for .IMD/.RPB sidecars next to
every Vantor stream COG (DigitalGlobe-style filenames trigger the reader); slow network made
each probe wait out full timeouts; (2) the segfault itself was a re-entrant double-open — the
welcome screen accepted a second double-click mid-load. Project file was fine.
Fix: `scripts/open_qgis.sh` launches the QGIS binary directly (not `open -a`) with
CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.tiff + GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR +
HTTP timeout caps, so non-.tif requests fail instantly. Load now completes in ~3 min of real
header fetches. qgis-mcp server auto-starts on load (listens on 9876 without clicking Start
Server). NB the pre-crash in-memory visibility changes (B7/B8/C7/C8 zone layers) were never
saved and are gone. Also: CLAUDE.md gained the "execute_code protocol" section (labeled calls,
in-memory only, never save via MCP).

Follow-up: the same GDAL options are now machine-default via `~/.gdal/gdalrc` (verified GDAL
loads it), so any launch path — Finder double-click included — is protected and
`scripts/open_qgis.sh` is optional. Delete that file to undo; add extensions to
CPL_VSIL_CURL_ALLOWED_EXTENSIONS if a future project streams non-.tif remote formats.
