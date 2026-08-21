# CLAUDE.md

Systematic landslide inventory for the 2026-06-24 Venezuela earthquakes, done in QGIS
(`qgis/geer_venezuela.qgz`, EPSG:4326, relative paths), driven through the `mcp__qgis__*` tools.
The GEER reconnaissance phase ended 2026-08-21; it's preserved at git tag `geer-phase`.

## Rules

- The project file and everything under `data/` are Lorne's. Never save the project, never
  write/delete on disk, never commit. In-memory QGIS changes are fine when asked in that message;
  Lorne saves or discards.
- One change per turn: do what was asked, report in ≤5 lines, stop. Don't chain unasked
  follow-ups — offer one as a single line if it matters.
- Ambiguity → take the smaller reading and say so. Ask only if readings differ materially.
- Minimal prose. No recaps of agreed context, no option surveys, no headers unless asked.
- Scripts only when a task is repeated or too big for MCP; Lorne runs them (QGIS console).
- After a substantive change, add one line to `LOG.md`.

## Project layout

Layer groups: `Inventory` (new systematic mapping) · `Reference mappings` (GEER candidates,
geer_mapping, GeoSyntec, USGS ground failure, 1999 Ávila — read-only) · imagery/terrain/basemaps
as before. Imagery layers are named `MM-DD · <gsd>m <sensor> · <location> · <id>`; AFTER imagery
is cached in `data/basemaps/` (gitignored); sources in `data/manifest.yaml`.

## Gotchas

- Don't edit a data file while QGIS has it open; remove the layer, edit, re-add.
- Project CRS must stay EPSG:4326 (QGIS resets it to the first layer's CRS on an empty project).
- Never right-click-remove a ZONE pointer node — GUI Remove deletes the layer everywhere.
