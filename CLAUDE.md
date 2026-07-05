# CLAUDE.md — operating notes for this repo

QGIS-based landslide reconnaissance for the 2026-06-24 Venezuela earthquakes. The work happens in
QGIS, driven interactively through the **qgis-mcp** plugin. There are no notebooks — that workflow
was retired (see PROGRESS.md).

## Connecting to QGIS

Work is done against the live QGIS instance via the `mcp__qgis__*` tools (arbitrary PyQGIS through
`execute_code`). The user must have QGIS open with `qgis/geer_venezuela.qgz` loaded and the
qgis-mcp dock's **Start Server** clicked (port 9876). `mcp__qgis__ping` confirms the connection.

## Project structure

`qgis/geer_venezuela.qgz` (EPSG:4326, relative paths) holds all layers. Groups top→bottom:
Imagery footprints (toggle), Candidates, Roads, NASA Disasters (Earthdata), USGS, Terrain &
Geology, AFTER — post-event imagery, Basemaps. Details in README.md.

- Post-event AFTER imagery is cached locally in `data/basemaps/` (gitignored, ~10 GB), named
  `AFTER — <location> · <sensor> <gsd>m · <id>`. BEFORE (Wayback) / TOPO (hillshade) / NASA
  services stream live.
- Candidate sites are one point layer (`data/landslide_candidates/…geojson`) with an integer
  `site_no` field, labeled by it.
- `src/geer_venezuela/` (catalog/terrain/geology/roads) fetches source data; run with `uv run
  python`. `viewer.py` is orphaned notebook-only code.

## Conventions & gotchas

- **Don't edit a data file while QGIS has it open** — QGIS caches it and flushes its copy back over
  external writes; `reload()`/`setDataSource()` serve the stale cache. Remove the layer(s) first,
  edit on disk, then re-add a fresh layer.
- Keep project CRS **EPSG:4326** — QGIS silently resets it to the first layer's CRS on an empty
  project; re-apply after adding layers.
- Keep "AFTER" in imagery layer names; treat all AOI locations equally (no "primary" location);
  layer on/off is the user's to toggle — don't design around default visibility.
- Update PROGRESS.md (running log) after substantive changes.
