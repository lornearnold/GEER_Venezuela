# Data provenance & how to get every layer

This project is designed so a collaborator can account for **every** layer in
`qgis/geer_venezuela.qgz` — each one is either committed to the repo, streamed live from an
online service, or a large file with a recorded download link.

The machine-readable source of truth is **[`data/manifest.yaml`](data/manifest.yaml)**. The same
provenance (source, license, download link, how-to) is also embedded in each layer's **QGIS
metadata** — in QGIS, open *Layer Properties → Metadata* on any layer to see it in-app.

## The three tiers

| Tier | Meaning | Collaborator action |
|---|---|---|
| **repo** | Committed to git (small vectors + the derived slope raster + imagery footprints) | None — present after `git clone` |
| **stream** | Live online service (NASA Disasters ImageServers, Esri Wayback/Hillshade) | None — loads when online |
| **download** | Too large for git (the post-event imagery COGs, ~10 GB now, growing) | Run one fetch command, below |

Current counts: **12 repo · 9 stream · 16 download** (15 Planet COGs + 1 Vantor mosaic).

## Getting the large imagery (`download` tier)

The Planet SkySat/Pelican COGs are public on
[Source Cooperative](https://source.coop/planet/venezuela-earthquake-2026-06-24) (CC BY-NC 4.0).
To pull everything the project references into `data/basemaps/`:

```bash
uv sync                                              # once, to get the Python env
uv run python -m geer_venezuela.manifest fetch       # downloads missing COGs (~10 GB)
```

`fetch` only downloads files that are missing; re-run any time. One file — the **Vantor Legion
mosaic** — is **not** directly downloadable (© Vantor, non-redistributable via NASA CSDA); it's
rebuilt by tiling the NASA ImageServer, and its manifest entry explains how. Everything else is a
direct HTTPS download.

## Auditing that nothing slipped through

```bash
uv run python -m geer_venezuela.manifest check       # project <-> manifest <-> disk
uv run python -m geer_venezuela.manifest list        # or: list repo|stream|download
```

`check` parses the `.qgz`, confirms **every layer in the project is catalogued** in the manifest,
and confirms every repo/download file the manifest names is on disk. Run it after adding layers.

## Adding new layers (incl. the growing external-drive imagery)

When you add imagery — including the ~100 GB you're staging on an external drive — keep it
accountable in two steps:

1. **Put the file under `data/basemaps/`** (see the external-drive note below) and add a row to
   `data/manifest.yaml`:
   ```yaml
   - name: AFTER — <location> · <sensor> <gsd>m · <id>   # must match the QGIS layer name
     tier: download
     path: data/basemaps/<file>.tif
     fetch: http
     url: https://…            # the public download link
     source: planet            # a key in the `sources:` block
   ```
2. **Re-embed metadata + re-audit.** Ask Claude (qgis-mcp) to refresh layer metadata from the
   manifest and save the project, then run `manifest check`.

### External-drive imagery — keeping paths portable

The project stores paths **relative to the `.qgz`** (e.g. `../data/basemaps/<file>.tif`), so all
imagery must resolve under `data/basemaps/` relative to the repo root. That keeps **one** set of
paths in the project that works on every machine. For 100 GB that can't live inside the repo
folder, make `data/basemaps` a **symlink** to wherever the bytes actually are:

```bash
# your machine — point the repo's basemaps dir at the external drive
mv data/basemaps /Volumes/GEER_Drive/basemaps        # (first time; or just create it there)
ln -s /Volumes/GEER_Drive/basemaps data/basemaps
```

The `.qgz` never changes — it always references `../data/basemaps/<file>`, which follows the
symlink to the drive. A collaborator without the drive instead lets `manifest fetch` download into
a real `data/basemaps/` directory (or symlinks it to their own storage). Because access is by
public re-download, **no one needs your physical drive** — the drive is just your local cache.

> `data/basemaps/` is gitignored except `imagery_footprints.geojson`, so the big COGs are never
> committed regardless of where they physically sit.

## Licensing summary

| Source | License / terms |
|---|---|
| Planet SkySat/Pelican COGs | CC BY-NC 4.0, © Planet Labs PBC |
| Vantor Legion mosaic | © Vantor — **non-redistributable** (NASA CSDA); viewing aid only |
| NASA Disasters ImageServers | NASA Earthdata open; products may carry Copernicus/USGS terms |
| Esri Wayback / Hillshade | Esri, Maxar, Airbus DS, etc. — Esri terms of use |
| OpenStreetMap roads | © OpenStreetMap contributors, ODbL 1.0 |
| USGS rapid assessment | USGS — public domain |
| Copernicus GLO-30 (slope) | Copernicus DEM — free/open |
| Geology (via Macrostrat) | Macrostrat CC-BY; source USGS OFR 2005-1038 |

Per-layer license and links live in `data/manifest.yaml` and each layer's QGIS metadata.
