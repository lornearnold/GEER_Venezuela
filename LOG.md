# Log

- 2026-08-21 — Tagged `geer-phase`; stripped src/notebooks/reports/scripts/docs; new CLAUDE.md, README, LOG.
- 2026-08-21 — data/ reorganized to mirror layer groups: reference/, inspection_grid/, imagery/ (was basemaps/); orphan GEER data removed (at tag geer-phase); 39 layers repointed in QGIS.
- 2026-08-21 — manifest.yaml regenerated from the live project (163 layers, 16 sources); old entries for removed layers dropped.
- 2026-08-22 — Added qgis/after_filter.py: toolbar "Filter AFTER to view" / "Show all AFTER" (Private-flag spatial filter via imagery_footprints); openProject macro set in memory (Lorne: enable macros, save). Replaces the ZONE viewer groups once validated.
- 2026-08-22 — Removed `viewer - AFTER imagery` (42 pointer groups) and `ZONE index — AFTER imagery` from the project (in memory; registry bridge disabled during removal). data/imagery/imagery_zones.geojson left on disk for Lorne to delete.
