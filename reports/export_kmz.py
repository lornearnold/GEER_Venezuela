"""Export all candidate sites to a KMZ, foldered by priority section and group.

Classification is shared with the report (reports/_classify.py) and derived from
the candidate attributes — no report_plan.json, so every site (including ones added
after the last packet build) is always covered.

    uv run python reports/export_site_data.py   # refresh attributes first
    uv run python reports/export_kmz.py
"""

from __future__ import annotations

import json
from pathlib import Path

import simplekml

import _classify as clf

HERE = Path(__file__).resolve().parent
OUT = HERE / "geer_venezuela_candidate_sites.kmz"


def description(s: dict) -> str:
    rows = [
        ("Group", s["group"] or "—"),
        ("Perishability estimate", s["perishability"] or "—"),
        ("Extent estimate", s["extent"] or "—"),
        ("Location", s["location"] or "—"),
        ("Approx. dist. to road (m)", s["road_dist_m"] if s["road_dist_m"] is not None else "—"),
        ("Notes", s["note"] or "—"),
    ]
    tr = "".join(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>" for k, v in rows)
    return (
        f"<table border='0' cellpadding='2'>{tr}</table>"
        "<p>GEER — 2026-06-24 Venezuela Earthquakes · candidate landslide site "
        "(flagged from satellite imagery; field verification required)</p>"
    )


def main() -> None:
    sites = json.loads((HERE / "site_data.json").read_text())["sites"]
    units = clf.build_units(sites)  # priority order, all sites

    kml = simplekml.Kml(name="GEER Venezuela — candidate landslide sites (2026-06-24 EQs)")

    style = simplekml.Style()
    style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
    style.iconstyle.color = simplekml.Color.rgb(255, 200, 0)  # match packet-map yellow
    style.iconstyle.scale = 0.9
    style.labelstyle.scale = 0.8

    section_folders: dict[int, simplekml.Folder] = {}
    for sec in sorted(clf.SECTION_NAMES):
        section_folders[sec] = kml.newfolder(name=clf.SECTION_NAMES[sec])

    n_points = 0
    for u in units:  # already in priority order
        parent = section_folders[u["section"]]
        if u["kind"] == "group":
            parent = parent.newfolder(name=f'Group: {u["key"]}')
        for no in u["site_nos"]:
            s = sites[str(no)]
            p = parent.newpoint(name=str(no), coords=[(s["lon"], s["lat"])],
                                description=description(s))
            p.style = style
            n_points += 1

    kml.savekmz(str(OUT))
    print(f"wrote {OUT.name}: {n_points} sites in {len(units)} units across "
          f"{len(clf.SECTION_NAMES)} priority folders")


if __name__ == "__main__":
    main()
