# Venezuela 2026 landslide inventory

QGIS project for a systematic landslide inventory along the Venezuela coast after the
2026-06-24 earthquakes. Open `qgis/geer_venezuela.qgz` (QGIS 3.x LTR, EPSG:4326).

- `data/` — vectors and small rasters used by the project; `data/manifest.yaml` records the
  source, license, and download link for every layer, including the ~10 GB post-event imagery
  cache (`data/basemaps/`, gitignored).
- `LOG.md` — one line per substantive change.

The earlier GEER reconnaissance phase (candidate sites, report, notebooks, scripts) is preserved
at git tag `geer-phase`.
