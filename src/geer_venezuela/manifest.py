"""Data manifest tooling for the GEER Venezuela QGIS project.

`data/manifest.yaml` records the provenance of every layer in
`qgis/geer_venezuela.qgz`, sorted into three tiers:

    repo      committed to git (present after clone)
    stream    live online service (loads when online, nothing to download)
    download  too large for git — fetch by HTTPS or rebuild

This module keeps the manifest honest and makes the download tier reproducible:

    uv run python -m geer_venezuela.manifest check   # audit project <-> manifest <-> disk
    uv run python -m geer_venezuela.manifest fetch    # download missing 'download' files
    uv run python -m geer_venezuela.manifest list [tier]

Adding a new layer? Add a row to data/manifest.yaml (a `download` row needs only
`name`, `path`, `fetch: http`, `url`), then run `fetch` to pull it and `check` to
confirm the project and manifest agree.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "manifest.yaml"
PROJECT = ROOT / "qgis" / "geer_venezuela.qgz"


def load() -> dict:
    with open(MANIFEST) as f:
        return yaml.safe_load(f)


def _ident(datasource: str) -> str:
    """A stable comparison key for a QGIS datasource or a manifest url/path.

    Files -> basename; tile/image services -> the url truncated at the first
    template token ({z}, ${z}, %7Bz%7D) so project and manifest forms match.
    """
    s = (datasource or "").strip()
    m = re.search(r"url=['\"]?([^'\"&\s]+)", s) or re.search(r"<ServerUrl>([^<]+)</ServerUrl>", s)
    if s.lower().startswith("http") or m:
        url = m.group(1) if m else s
        return re.split(r"\$?\{|%7[bB]", url)[0].rstrip("/")
    path = s.split("|", 1)[0]  # strip |layername=, |subset=, etc.
    return Path(path).name


def project_datasources() -> list[tuple[str, str]]:
    """(layer name, datasource) for every map layer in the .qgz project."""
    with zipfile.ZipFile(PROJECT) as z:
        qgs = next(n for n in z.namelist() if n.endswith(".qgs"))
        tree = ElementTree.fromstring(z.read(qgs))
    out = []
    for ml in tree.iter("maplayer"):
        name = (ml.findtext("layername") or "?").strip()
        ds = (ml.findtext("datasource") or "").strip()
        out.append((name, ds))
    return out


def check() -> int:
    doc = load()
    layers = doc["layers"]
    by_ident = {}
    for lyr in layers:
        # download entries have both path and url; identify them by the local file.
        by_ident.setdefault(_ident(lyr.get("path") or lyr.get("url", "")), lyr)

    problems = 0

    # 1. Every layer in the live project must be catalogued in the manifest.
    print("== project layers vs manifest ==")
    for name, ds in project_datasources():
        ident = _ident(ds)
        if ident in by_ident:
            continue
        problems += 1
        print(f"  UNCATALOGUED  {name}\n                {ds[:90]}")
    if problems == 0:
        print("  all project layers are in the manifest ✓")

    # 2. Every repo/download file the manifest names must exist on disk.
    print("\n== manifest files on disk ==")
    missing_repo, missing_dl = [], []
    for lyr in layers:
        if "path" not in lyr:
            continue
        exists = (ROOT / lyr["path"]).exists()
        if exists:
            continue
        (missing_dl if lyr["tier"] == "download" else missing_repo).append(lyr)

    for lyr in missing_repo:
        problems += 1
        print(f"  MISSING (repo!)  {lyr['path']}  — should be committed but is absent")
    if missing_dl:
        print(f"  {len(missing_dl)} download-tier file(s) not present locally "
              f"(expected until you fetch) — run: manifest fetch")
        for lyr in missing_dl:
            how = lyr.get("fetch", "?")
            print(f"      {lyr['path']}  [{how}]")
    if not missing_repo and not missing_dl:
        print("  every manifest file is present ✓")

    n = {t: sum(1 for l in layers if l["tier"] == t) for t in ("repo", "stream", "download")}
    print(f"\n{len(layers)} layers: {n['repo']} repo, {n['stream']} stream, {n['download']} download")
    print("PROBLEMS:" if problems else "OK — manifest and project agree.", problems or "")
    return 1 if problems else 0


def fetch(force: bool = False) -> int:
    doc = load()
    targets = [l for l in doc["layers"]
               if l.get("tier") == "download" and l.get("fetch") == "http" and l.get("url")]
    rebuilds = [l for l in doc["layers"]
                if l.get("tier") == "download" and l.get("fetch") == "rebuild"]
    todo = [l for l in targets if force or not (ROOT / l["path"]).exists()]

    print(f"{len(targets)} HTTPS download-tier files; {len(todo)} to fetch"
          f"{' (--force)' if force else ' (missing only)'}.")
    for i, lyr in enumerate(todo, 1):
        dest = ROOT / lyr["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        print(f"[{i}/{len(todo)}] {lyr['path']}\n         <- {lyr['url']}")
        try:
            urllib.request.urlretrieve(lyr["url"], tmp)
            tmp.replace(dest)
        except Exception as e:
            if tmp.exists():
                tmp.unlink()
            print(f"         FAILED: {e}")
            return 1
    if rebuilds:
        print(f"\n{len(rebuilds)} file(s) are NOT directly downloadable (fetch: rebuild):")
        for lyr in rebuilds:
            print(f"    {lyr['path']} — {lyr.get('note', 'see manifest note')}")
    print("done.")
    return 0


def list_layers(tier: str | None = None) -> int:
    doc = load()
    srcs = doc.get("sources", {})
    for lyr in doc["layers"]:
        if tier and lyr["tier"] != tier:
            continue
        loc = lyr.get("path") or lyr.get("url", "")
        lic = srcs.get(lyr.get("source"), {}).get("license", "")
        print(f"[{lyr['tier']:>8}] {lyr['name']}\n           {loc}" + (f"\n           {lic}" if lic else ""))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="audit project <-> manifest <-> disk")
    fp = sub.add_parser("fetch", help="download missing download-tier files")
    fp.add_argument("--force", action="store_true", help="re-download even if present")
    lp = sub.add_parser("list", help="list layers, optionally filtered by tier")
    lp.add_argument("tier", nargs="?", choices=["repo", "stream", "download"])
    args = p.parse_args(argv)
    if args.cmd == "check":
        return check()
    if args.cmd == "fetch":
        return fetch(force=args.force)
    if args.cmd == "list":
        return list_layers(args.tier)
    return 2


if __name__ == "__main__":
    sys.exit(main())
