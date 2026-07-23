"""Assemble the route-map report PDF (one page per field-trip route).

Pipeline: route_data.json (build_route_data.py) + per-route figure metadata
(figures/manifest.json, produced by the QGIS render step) -> route_pages.json ->
compile report_routes.typ.

    uv run python reports/routes/build_route_data.py        # refresh route_data.json first
    uv run python reports/routes/build_route_report.py      # then this

Routes without a figure in the manifest are reported as UNRENDERED (render them in QGIS
first) unless --allow-missing is passed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "report_routes.pdf"), help="output PDF path")
    ap.add_argument("--allow-missing", action="store_true",
                    help="skip routes with no figure yet instead of erroring")
    ap.add_argument("--no-compile", action="store_true", help="write route_pages.json only")
    args = ap.parse_args()

    routes = json.loads((HERE / "route_data.json").read_text())["routes"]
    manifest = json.loads((HERE / "figures/manifest.json").read_text())
    mfu = manifest["units"]

    missing = [r["key"] for r in routes if r["key"] not in mfu]
    if missing and not args.allow_missing:
        print("Routes needing a figure — render these in QGIS first:", file=sys.stderr)
        for k in missing:
            print(f"  {k!r}", file=sys.stderr)
        sys.exit(1)

    units, skipped = [], 0
    for r in routes:
        m = mfu.get(r["key"])
        if m is None:
            skipped += 1
            continue
        units.append({
            "key": r["key"],
            "fig": m["fig"],
            "map_scale": m["scale"],
            "bar_m": m["bar_m"],
        })

    (HERE / "route_pages.json").write_text(
        json.dumps({"units": units}, ensure_ascii=False, indent=1))
    print(f"route_pages.json: {len(units)} pages"
          + (f", {skipped} skipped (no figure)" if skipped else ""))

    if args.no_compile:
        return
    # report_routes.typ imports ../template.typ, so the compile root must be reports/
    # (Typst forbids reading files outside the project root).
    root = HERE.parent
    subprocess.run(
        ["typst", "compile", "--root", str(root), str(HERE / "report_routes.typ"), args.out],
        check=True)
    print(f"compiled -> {args.out}")


if __name__ == "__main__":
    main()
