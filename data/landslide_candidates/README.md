# Landslide candidate sites — data sources

Suspected-landslide points marked in QGIS by comparing pre- and post-earthquake imagery. Each
feature carries an integer **`site_no`** (1…N, labeled on the map) plus `category` and `note`
fields for confidence and observations. Points span the impacted coast (the USGS assessment AOI);
they load directly in QGIS, ArcGIS Online, and Google Earth (KMZ).

Marking was done against:

- **After**: Planet SkySat / Pelican post-event scenes (25–28 June 2026, 0.42–0.87 m), plus the
  NASA Vantor Legion 0.42 m mosaic. © Planet Labs PBC (CC BY-NC 4.0) / © Vantor (non-redistributable).
  The earliest points were marked on Pelican scene `20260626_150535_17_3010` (La Guaira).
- **Before**: Esri World Imagery Wayback, release 2026-05-28. Underlying captures vary by tile
  (2024 – early 2025 over most of the coast; Maxar WorldView-2 / GeoEye-1, ~0.3–0.5 m).

Earlier drafts distinguished points (lower confidence) from polygons (moderate confidence); the
polygons were later converted to points near their centroids, so the layer is now points only.

## References

- Planet Crisis Response — Venezuela Earthquake 2026-06-24:
  https://source.coop/planet/venezuela-earthquake-2026-06-24
- Esri World Imagery Wayback (per-tile capture dates): https://livingatlas.arcgis.com/wayback/
