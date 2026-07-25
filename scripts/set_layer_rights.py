"""Write licence/attribution metadata onto every imagery layer from the manifest.

Run inside QGIS: Plugins > Python Console > Show Editor > open this > Run.
Then save the project (Ctrl+S) if the report looks right.

Why this exists
---------------
`data/manifest.yaml` records the licence of every layer via its `source:` key,
but that text was only ever embedded into a subset of the layers. The rest carry
no rights metadata at all, so anything reading `layer.metadata().rights()` -- the
Identify panel, layer properties, and the `imagery_label()` decoration function
in scripts/qgis_expression_functions.py -- shows a blank source.

This fills the gap from the manifest, which stays the single source of truth.
Nothing is invented here: a layer with no manifest entry is reported and skipped
rather than guessed at.

Matching
--------
Layers are matched to manifest rows by **datasource**, not by name, reusing the
manifest module's own `_ident()` key so the two agree exactly. Renaming a layer
in QGIS therefore does not break the match.

Idempotent -- re-run after adding layers. Set DRY_RUN = False to actually write;
it starts True so the first run only reports what would change.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from qgis.core import (
    QgsDateTimeRange,
    QgsLayerMetadata,
    QgsProject,
    QgsRasterLayer,
)
from qgis.PyQt.QtCore import QDate, QDateTime, QTime

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifest.yaml"

# YYYY-MM-DD anywhere in a layer or source name.
_DATE_RE = re.compile(r"((?:19|20)\d{2})-(\d{2})-(\d{2})")


def _ident(datasource: str) -> str:
    """Stable comparison key for a datasource or manifest url/path.

    Copied from geer_venezuela.manifest so this script runs under the QGIS
    interpreter, which cannot import the repo's uv venv modules. Keep the two
    in sync: files -> basename, services -> url truncated at the first template
    token so project and manifest forms match.
    """
    s = (datasource or "").strip()
    s = re.sub(r"^/vsi(curl|s3|gs|az)(_streaming)?/", "", s)
    m = re.search(r"url=['\"]?([^'\"&\s]+)", s) or re.search(r"<ServerUrl>([^<]+)</ServerUrl>", s)
    if s.lower().startswith("http") or m:
        url = m.group(1) if m else s
        return re.split(r"\$?\{|%7[bB]", url)[0].rstrip("/")
    path = s.split("|", 1)[0]
    return Path(path).name


def _manifest_index() -> tuple[dict, dict]:
    """(ident -> layer row, source key -> source block) from the manifest."""
    with open(MANIFEST) as f:
        doc = yaml.safe_load(f)
    sources = doc.get("sources", {})
    by_ident = {}
    for row in doc.get("layers", []):
        key = _ident(row.get("path") or row.get("url", ""))
        if key:
            by_ident.setdefault(key, row)
    return by_ident, sources


def _release_date(layer_name: str, source_block: dict):
    """A YYYY-MM-DD date from the layer name, else from the manifest source name.

    Used only for always-on service layers, which carry no temporal properties;
    see the note in _stamp_temporal_extent.
    """
    for text in (layer_name, source_block.get("name", "")):
        match = _DATE_RE.search(text or "")
        if match:
            year, month, day = (int(g) for g in match.groups())
            try:
                return QDate(year, month, day)
            except ValueError:
                continue
    return None


def _stamp_temporal_extent(layer, metadata, qdate) -> bool:
    """Record a one-day temporal extent in the layer's *metadata*.

    Deliberately not temporalProperties(): scripts/imagery_index.py keeps
    service layers (Wayback, NASA, hillshade) off the Temporal Controller so
    they stay visible at every point on the timeline. The metadata extent is a
    separate slot, so a date can be published for the decoration label without
    putting the layer on the time slider.
    """
    extent = metadata.extent()
    if extent.temporalExtents():
        return False
    begin = QDateTime(qdate, QTime(0, 0))
    end = QDateTime(qdate.addDays(1), QTime(0, 0))
    extent.setTemporalExtents([QgsDateTimeRange(begin, end)])
    metadata.setExtent(extent)
    return True


def apply_rights(dry_run: bool = True) -> int:
    project = QgsProject.instance()
    by_ident, sources = _manifest_index()

    written, already, unmatched, no_licence, dated = [], [], [], [], []

    for layer in project.mapLayers().values():
        if not isinstance(layer, QgsRasterLayer):
            continue

        row = by_ident.get(_ident(layer.source()))
        if row is None:
            unmatched.append(layer.name())
            continue

        source_key = row.get("source")
        source_block = sources.get(source_key, {})
        licence = source_block.get("license", "")
        if not licence:
            no_licence.append((layer.name(), source_key))
            continue

        metadata = layer.metadata()
        changed = False

        if metadata.rights() != [licence]:
            metadata.setRights([licence])
            metadata.setLicenses([licence])
            written.append((layer.name(), licence))
            changed = True

        # Only layers with no temporal properties need the metadata fallback.
        temporal = layer.temporalProperties()
        if not temporal.isActive():
            qdate = _release_date(layer.name(), source_block)
            if qdate and _stamp_temporal_extent(layer, metadata, qdate):
                dated.append((layer.name(), qdate.toString("yyyy-MM-dd")))
                changed = True

        if not changed:
            already.append(layer.name())
        elif not dry_run:
            layer.setMetadata(metadata)

    verb = "would set" if dry_run else "set"
    print(f"{verb} rights on {len(written)} raster layer(s)")
    for name, licence in written[:8]:
        print(f"    {name[:56]}\n        {licence}")
    if len(written) > 8:
        print(f"    ... and {len(written) - 8} more")

    if dated:
        print(f"\n{verb} a metadata date on {len(dated)} always-on service layer(s)")
        for name, day in dated:
            print(f"    {name[:56]}  ->  {day}")

    print(f"\nalready correct : {len(already)}")
    if no_licence:
        print(f"manifest row has no licence text : {len(no_licence)}")
        for name, key in no_licence[:5]:
            print(f"    {name[:56]}  (source: {key})")
    if unmatched:
        print(f"\nNOT IN MANIFEST : {len(unmatched)} -- add rows for these, then re-run")
        for name in unmatched[:10]:
            print(f"    {name[:70]}")
        if len(unmatched) > 10:
            print(f"    ... and {len(unmatched) - 10} more")

    if dry_run:
        print("\nDRY RUN -- nothing written. Set DRY_RUN = False and re-run to apply.")
    else:
        print("\nWritten to the layers in memory. Save the project (Ctrl+S) to persist.")
    return 0


# Start safe: report first, write only once you have seen the report.
DRY_RUN = False

# No __main__ guard: the QGIS console's Run button does not set __name__ to
# "__main__", so a guarded call would silently do nothing.
apply_rights(dry_run=DRY_RUN)
