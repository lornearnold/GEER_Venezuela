# Trimming the 1999 Vargas mosaics with a crop polygon

The georeferenced 1999 aerial mosaics carry an opaque scanned-paper margin (and black photo-frame
gaps) around the actual imagery, which obscures whatever is underneath them in QGIS. The fix is to
draw a polygon around the real photo coverage and clip each raster to it.

> An automated flood-fill was tried first and rejected — it removed interior image content along
> with the edges. Draw the boundary by hand instead; the imagery inside the polygon is never touched.

## The layers

| Layer (in **Basemaps** group) | File (`data/basemaps/historical_1999_vargas/`) |
|---|---|
| `BEFORE-1999 — camuri-caraballeda · aerial mosaic 15k · 1999-12-27` | `BEFORE-1999 — camuri-caraballeda · aerial mosaic 15k · 1999-12-27.tif` |
| `BEFORE-1999 — vargas coast · aerial mosaic 15k · 1999-12-27` | `BEFORE-1999 — vargas coast · aerial mosaic 15k · 1999-12-27.tif` |

Both are EPSG:4326, grey + alpha, regenerated from the original scans via the saved GCPs.

## Steps

1. **Show the mosaic.** Turn on the `BEFORE-1999 — camuri-caraballeda…` layer in the Basemaps group
   and zoom to it (right-click → Zoom to Layer).

2. **Create the polygon layer.**
   - *Layer → Create Layer → New GeoPackage Layer…*
   - Geometry type: **Polygon**
   - CRS: **EPSG:4326**
   - Name: `crop_1999_camuri`, saved into `data/basemaps/historical_1999_vargas/`

3. **Draw the crop boundary.**
   - Select the new layer → **Toggle Editing** (pencil icon)
   - Pick **Add Polygon Feature**
   - Click around the outline of the actual photo mosaic — inside the paper margin, following where
     the real aerial photos are. Left-click each vertex, **right-click to finish**.
   - It doesn't need to be surgical. A rough many-sided polygon is fine; follow the ragged edge as
     loosely or tightly as you like.
   - **Toggle Editing off**, and save when prompted.

4. **Repeat for the second mosaic** (`crop_1999_vargas`), or add it as a **second feature in the same
   layer** — either works, they can be matched to their rasters by which one they overlap.

5. **Hand it back to Claude** with the layer name/path, and it will clip each mosaic to its polygon.

## What the clip does (for reference)

Lossless `gdalwarp -cutline` against the polygon, with `-dstalpha` so everything outside the polygon
becomes transparent. Pixels inside are copied through untouched (no resampling loss, no
recompression artifacts), then overviews are rebuilt:

```sh
QBIN=/Applications/QGIS-LTR.app/Contents/MacOS
export DYLD_LIBRARY_PATH=$QBIN/lib \
       GDAL_DATA=/Applications/QGIS-LTR.app/Contents/Resources/qgis/gdal \
       PROJ_LIB=/Applications/QGIS-LTR.app/Contents/Resources/qgis/proj \
       PROJ_DATA=$PROJ_LIB

"$QBIN/gdalwarp" -cutline crop_1999_camuri.gpkg -dstalpha -overwrite \
  -co COMPRESS=DEFLATE -co PREDICTOR=2 -co TILED=YES \
  "BEFORE-1999 — camuri-caraballeda · aerial mosaic 15k · 1999-12-27.tif" out.tif
"$QBIN/gdaladdo" -r average out.tif 2 4 8 16
```

Note the QGIS-bundled GDAL 3.12 is used deliberately — the `gdal_translate` on PATH is GDAL 3.3 from
Postgres.app and lacks codecs; the `/qgis/` segment in `GDAL_DATA`/`PROJ_LIB` is required or PROJ
can't find `proj.db` and the CRS gets dropped.

## Rebuilding from scratch, if ever needed

The original scans and the georeferencing control points are both kept in
`data/basemaps/historical_1999_vargas/` (gitignored), so either mosaic can be regenerated:

- `Camuri_Chco-Cerro_Grande.jpg` + `Camuri_Chco-Cerro_Grande.jpg.points` (17 GCPs)
- `Mosvar.tif` + `Mosvar.tif.points` (48 GCPs)

Recipe: `gdal_translate -a_srs EPSG:4326` with `-gcp` args built from the `.points` file (note the
QGIS georeferencer writes `sourceY` negative, so pass `-gcp <sourceX> <-sourceY> <mapX> <mapY>`),
then `gdalwarp -r cubic -tps -t_srs EPSG:4326 -dstalpha`.
