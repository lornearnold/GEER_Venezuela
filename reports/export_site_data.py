"""Export candidate-site attributes to reports/site_data.json for the Typst summaries.

The Typst template (site_summary.typ) references sites by site_no only; all table
content (perishability, extent, coordinates, road distance, notes, group) comes from
this JSON. Re-run after editing the candidates layer in QGIS:

    uv run python reports/export_site_data.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CANDIDATES = REPO / "data/landslide_candidates/la-guaira_20260626_150535_17_3010.geojson"
OUT = REPO / "reports/site_data.json"


def main() -> None:
    features = json.loads(CANDIDATES.read_text())["features"]

    sites: dict[str, dict] = {}
    for f in features:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        sites[str(p["site_no"])] = {
            "group": p.get("group"),
            "perishability": p.get("perishability") or "",
            "location": p.get("location") or "",
            "extent": p.get("extent") or "",
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "road_dist_m": p.get("road_dist_m"),
            "note": p.get("note") or "",
        }

    OUT.write_text(json.dumps(
        {"generated": date.today().isoformat(), "source": CANDIDATES.name, "sites": sites},
        indent=1,
    ))

    groups: dict[str, int] = {}
    for s in sites.values():
        groups[s["group"] or "(ungrouped)"] = groups.get(s["group"] or "(ungrouped)", 0) + 1
    print(f"wrote {OUT.relative_to(REPO)}: {len(sites)} sites, groups: {groups}")


if __name__ == "__main__":
    main()
