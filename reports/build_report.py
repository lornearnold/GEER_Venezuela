"""Assemble a report or supplement PDF from the candidate data — no separate plan.

Pipeline: classify sites into priority units (reports/_classify.py, derived from
attributes) → join each unit to its render metadata (reports/figures/manifest.json,
produced by the /geer-report render step) → write reports/build/pages.json → compile
report.typ.

    uv run python reports/build_report.py --mode full
    uv run python reports/build_report.py --mode supplement --label "Supplement 1" --sites 111-123
    uv run python reports/build_report.py --mode supplement --sites 3,4,94 --out reports/supplement_2.pdf

`--sites` accepts all | a list (3,4,94) | ranges (111-123) | a mix. A group is pulled
in whole if any member is selected. Units without a figure in the manifest are reported
as UNRENDERED — run the /geer-report render step for them first (or pass --allow-missing
to skip them).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import _classify as clf

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["full", "supplement"], required=True)
    ap.add_argument("--label", help="document badge for a supplement, e.g. 'Supplement 1'")
    ap.add_argument("--sites", default="all", help="all | 3,4,94 | 111-123 | mix")
    ap.add_argument("--out", help="output PDF path (default: report.pdf / supplement.pdf)")
    ap.add_argument("--allow-missing", action="store_true",
                    help="skip units that have no figure yet instead of erroring")
    ap.add_argument("--no-compile", action="store_true", help="write pages.json only")
    args = ap.parse_args()

    sites = json.loads((HERE / "site_data.json").read_text())["sites"]
    manifest = json.loads((HERE / "figures/manifest.json").read_text())
    mfu = manifest["units"]

    selection = clf.parse_selection(args.sites, sites)
    units = clf.build_units(sites, selection)

    # A unit needs (re)rendering if it has no figure yet, OR its membership changed
    # since the figure was made (e.g. a site was added to an existing group) — detected
    # by comparing the manifest's stored site_nos against the freshly classified ones.
    needs = []
    for u in units:
        m = mfu.get(u["key"])
        if m is None:
            needs.append((u, "no figure yet"))
        elif sorted(m.get("site_nos", [])) != sorted(u["site_nos"]):
            needs.append((u, f"membership changed {sorted(m.get('site_nos', []))} -> {u['site_nos']}"))
    if needs and not args.allow_missing:
        print("Units needing (re)render — run /geer-report for these first:", file=sys.stderr)
        for u, why in needs:
            print(f"  {u['key']!r} (sec{u['section']}, sites {u['site_nos']}) — {why}", file=sys.stderr)
        sys.exit(1)
    skipped = stale = 0

    pages = []
    for u in units:
        m = mfu.get(u["key"])
        if m is None:
            skipped += 1  # --allow-missing: no figure, drop the page
            continue
        if sorted(m.get("site_nos", [])) != sorted(u["site_nos"]):
            stale += 1  # --allow-missing: figure predates a membership change
        pages.append({
            "title": u["title"],
            "site_nos": u["site_nos"],
            "fig": m["fig"],
            "locator": m["locator"],
            "map_scale": m["scale"],
            "locator_scale": m["locator_scale"],
            "bar_m": m["bar_m"],
            "imagery": m["credit"],
        })

    doc_label = None
    cover = None
    if args.mode == "supplement":
        doc_label = args.label or "Supplement 1"
    else:
        cover = manifest.get("cover")

    BUILD.mkdir(exist_ok=True)
    (BUILD / "pages.json").write_text(json.dumps(
        {"doc_label": doc_label, "cover": cover, "units": pages}, ensure_ascii=False, indent=1))
    print(f"pages.json: {len(pages)} pages"
          + (f", {skipped} skipped (no figure)" if skipped else "")
          + (f", {stale} STALE figure (membership changed)" if stale else "")
          + (", cover" if cover else "") + (f", badge {doc_label!r}" if doc_label else ""))

    if args.no_compile:
        return
    out = args.out or str(HERE / ("report.pdf" if args.mode == "full" else "supplement.pdf"))
    subprocess.run(["typst", "compile", str(HERE / "report.typ"), out], check=True)
    print(f"compiled -> {out}")


if __name__ == "__main__":
    main()
