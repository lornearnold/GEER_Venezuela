"""Assemble per-route data for the route-map report.

Source of truth:
  - data/routes/field_trips/{r*}_line.geojson       route line + trip metadata (start/end/km)
  - data/routes/field_trips/{r*}_endpoints.geojson  start/end points + labels
  - data/routes/field_trips/trip_sites.geojson      all trip POIs (site_no, location, slope, aspect)

Route -> POI membership comes from the original planning note (_temp.md), transcribed
here as ROUTE_POIS. Ordering is visit order along the route.

Writes reports/routes/route_data.json consumed by reports/routes/report_routes.typ.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FT = REPO / "data/routes/field_trips"
OUT = Path(__file__).resolve().parent / "route_data.json"

# Route key -> ordered list of POI site numbers to visit (from _temp.md).
ROUTE_POIS = {
    "r1": [93, 94, 86],
    "r2": [25, 4],
    "r3": [125],
    "r4": [124, 105, 79, 80, 81, 78],
    "r5": [57, 58, 55, 49, 1, 2, 4, 24, 48],
    "r5alt": [57, 58, 55, 49, 1, 2, 4, 25, 97, 98, 99, 100, 101, 102, 24, 48],
}

# Display order of route pages in the report.
ROUTE_ORDER = ["r1", "r2", "r3", "r4", "r5", "r5alt"]


def load_sites() -> dict[int, dict]:
    d = json.loads((FT / "trip_sites.geojson").read_text())
    out = {}
    for ft in d["features"]:
        p = ft["properties"]
        lon, lat = ft["geometry"]["coordinates"]
        out[int(p["site_no"])] = {
            "site_no": int(p["site_no"]),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "location": p.get("location"),
            "slope_deg": p.get("slope_deg"),
            "aspect_dir": p.get("aspect_dir"),
        }
    return out


def main() -> None:
    sites = load_sites()
    routes = []
    for key in ROUTE_ORDER:
        line = json.loads((FT / f"{key}_line.geojson").read_text())["features"][0]["properties"]
        pois = []
        for no in ROUTE_POIS[key]:
            if no not in sites:
                raise SystemExit(f"{key}: POI site {no} not found in trip_sites.geojson")
            pois.append(sites[no])
        routes.append({
            "key": key,
            "trip": line["trip"],          # e.g. "R1 — El Junquito Ridge"
            "start": line["start"],
            "end": line["end"],
            "km": line["km"],
            "poi_nos": ROUTE_POIS[key],
            "pois": pois,
        })

    OUT.write_text(json.dumps({"routes": routes}, ensure_ascii=False, indent=1))
    n_poi = sum(len(r["pois"]) for r in routes)
    print(f"route_data.json: {len(routes)} routes, {n_poi} POI rows -> {OUT}")


if __name__ == "__main__":
    main()
