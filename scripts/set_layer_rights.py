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
from pathlib import Path

import yaml
from qgis.core import QgsProject, QgsRasterLayer

def _repo_root() -> Path:
    """Repo root, found from the open project rather than from __file__.

    The QGIS console's Run button executes a *copy* of the script from a temp
    directory, so Path(__file__).parents[1] can land in /private/var/folders/...
    The loaded .qgz lives at <repo>/qgis/geer_venezuela.qgz, which is stable
    however the script was launched; __file__ is only a fallback for running it
    outside QGIS.
    """
    project_path = QgsProject.instance().fileName()
    if project_path:
        candidate = Path(project_path).resolve().parents[1]
        if (candidate / "data" / "manifest.yaml").exists():
            return candidate
    try:
        return Path(__file__).resolve().parents[1]
    except NameError:  # exec'd without __file__
        return Path.cwd()


ROOT = _repo_root()
MANIFEST = ROOT / "data" / "manifest.yaml"


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


# NOTE: an earlier version also stamped a one-day range into the layer's
# metadata extent so always-on service layers (Wayback) could report a date.
# That was removed: reading it back via
# layer.metadata().extent().temporalExtents() hard-crashes QGIS 3.44 with a
# SIGSEGV (freed temporary QgsLayerMetadata), and writing a value that cannot
# be read safely is worse than having no value. See the warning in
# scripts/qgis_expression_functions.py:_date_of.


def apply_rights(dry_run: bool = True) -> int:
    project = QgsProject.instance()
    by_ident, sources = _manifest_index()

    written, already, unmatched, no_licence = [], [], [], []

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
        if metadata.rights() == [licence]:
            already.append(layer.name())
            continue

        metadata.setRights([licence])
        metadata.setLicenses([licence])
        written.append((layer.name(), licence))
        if not dry_run:
            layer.setMetadata(metadata)

    verb = "would set" if dry_run else "set"
    print(f"{verb} rights on {len(written)} raster layer(s)")
    for name, licence in written[:8]:
        print(f"    {name[:56]}\n        {licence}")
    if len(written) > 8:
        print(f"    ... and {len(written) - 8} more")

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
