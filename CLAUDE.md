# CLAUDE.md — operating notes for this repo

QGIS-based landslide reconnaissance for the 2026-06-24 Venezuela earthquakes. The work happens in
QGIS, driven interactively through the **qgis-mcp** plugin. There are no notebooks — that workflow
was retired (see PROGRESS.md).

## Connecting to QGIS

Work is done against the live QGIS instance via the `mcp__qgis__*` tools (arbitrary PyQGIS through
`execute_code`). The user must have QGIS open with `qgis/geer_venezuela.qgz` loaded and the
qgis-mcp dock's **Start Server** clicked (port 9876). `mcp__qgis__ping` confirms the connection.

### execute_code protocol (agreed 2026-07-29)

- **Label every call** in the message text immediately before it, one line:
  `READ-ONLY: <what it inspects>` or `MUTATES (in-memory): <what changes>, no save`.
- Allowed via `execute_code`: labeled read-only diagnostics, and labeled **in-memory** changes
  the user explicitly requested (visibility, selection, canvas, temporal state).
- **Hard lines, never via MCP regardless of label**: `save_project`; adding/removing layers;
  editing features/fields/data files; writing to disk; overwriting styles. Those are delivered
  as a script in `scripts/` (run via `exec()` in the QGIS console) or as GUI steps.
- Dedicated typed `mcp__qgis__*` tools are fine as-is; still never call `save_project` — saving
  is always the user's click.

## Project structure

`qgis/geer_venezuela.qgz` (EPSG:4326, relative paths) holds all layers. Groups top→bottom:
Imagery footprints (toggle), Candidates, Roads, NASA Disasters (Earthdata), USGS, Terrain &
Geology, AFTER — post-event imagery, Basemaps. Details in README.md.

- Post-event AFTER imagery is cached locally in `data/basemaps/` (gitignored, ~10 GB). BEFORE
  (Wayback) / TOPO (hillshade) / NASA services stream live. Imagery **layers** are named
  `MM-DD · <gsd>m <sensor> · <location> · <id>` (BEFORE layers use full YYYY-MM-DD) — no era
  prefix; the AFTER/BEFORE group and zone names carry that. Alphabetical = chronological.
- **ZONES — AFTER imagery (index)**: 0.25° grid-cell groups (`B8 · la-guaira`; letter=row from
  north, number=column from west, anchor NW -69.0/11.0) holding *pointer nodes* to intersecting
  AFTER layers, + labeled `data/derived/imagery_zones.geojson` on canvas. Rebuild with
  `scripts/build_imagery_zones.py`; renames via `scripts/rename_imagery_layers.py`.
  **Never right-click-remove a pointer or zone group** — GUI Remove deletes the layers everywhere.
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
- Treat all AOI locations equally (no "primary" location); layer on/off is the user's to
  toggle — don't design around default visibility.
- Update PROGRESS.md (running log) after substantive changes.
