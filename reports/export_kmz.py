"""Export all candidate sites to a KMZ that mirrors the field packet's priority order.

Reads site_data.json (attributes) and report_plan.json (section/unit order built from
the QGIS project). Placemarks are foldered by priority section, with group sub-folders,
and styled like the packet maps (yellow dot, site_no label).

    uv run python reports/export_kmz.py
"""

from __future__ import annotations

import json
from pathlib import Path

import simplekml

HERE = Path(__file__).resolve().parent
OUT = HERE / "geer_venezuela_candidate_sites.kmz"

SECTION_NAMES = {
    2: "Priority 1 — high perishability (populated)",
    3: "Priority 2 — medium perishability (populated)",
    4: "Priority 3 — medium perishability (remote)",
    5: "Priority 4 — other sites",
    6: "Priority 5 — ungrouped low-confidence sites",
}


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
    units = json.loads((HERE / "report_plan.json").read_text())["units"]

    kml = simplekml.Kml(name="GEER Venezuela — candidate landslide sites (2026-06-24 EQs)")

    style = simplekml.Style()
    style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
    style.iconstyle.color = simplekml.Color.rgb(255, 200, 0)  # match packet-map yellow
    style.iconstyle.scale = 0.9
    style.labelstyle.scale = 0.8

    section_folders: dict[int, simplekml.Folder] = {}
    for sec in sorted(SECTION_NAMES):
        section_folders[sec] = kml.newfolder(name=SECTION_NAMES[sec])

    n_points = 0
    for u in units:  # already in packet order
        parent = section_folders[u["section"]]
        if u["kind"] == "group":
            parent = parent.newfolder(name=f'Group: {u["key"]}')
        for no in u["site_nos"]:
            s = sites[str(no)]
            p = parent.newpoint(
                name=str(no),
                coords=[(s["lon"], s["lat"])],
                description=description(s),
            )
            p.style = style
            n_points += 1

    kml.savekmz(str(OUT))
    print(f"wrote {OUT.name}: {n_points} sites in {len(units)} units across "
          f"{len(SECTION_NAMES)} priority folders")


if __name__ == "__main__":
    main()
