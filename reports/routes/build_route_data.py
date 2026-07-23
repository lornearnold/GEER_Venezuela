"""Assemble per-route data for the route-map report.

Source of truth:
  - data/routes/field_trips/{r*}_line.geojson       route line + trip metadata (start/end/km)
  - data/routes/field_trips/{r*}_endpoints.geojson  start/end points + labels
  - data/routes/field_trips/trip_sites.geojson      all trip POIs (site_no + coordinates)
  - reports/site_data.json                          candidate-site attributes for the report
    table (perishability / extent / road_dist_m / note), same fields as the main report.

POI table columns mirror the main candidate report; per-site values are joined from
site_data.json by site_no. A field-trip POI that is not a candidate site (e.g. 124, 125)
has no site_data.json row — its attribute cells fall back to null and render as "—".

Route -> POI membership comes from the original planning note (_temp.md), transcribed
here as ROUTE_POIS. Ordering is visit order along the route.

Writes reports/routes/route_data.json consumed by reports/routes/report_routes.typ.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FT = REPO / "data/routes/field_trips"
SITE_DATA = REPO / "reports/site_data.json"
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

# Report page order + title. The route pages are numbered "Route 1".."Route N" in the
# order the field-trip groups were arranged in QGIS (which is not the r1..r5 file order):
#   Route 1 = r4, Route 2 = r3, Route 3 = r5, Route 4 = r1, Route 5 = r2.
# r5alt (Airport Loop via Trocha) is intentionally not published. The title here overrides
# the geojson `trip` attribute so renaming a page is a one-line change and never depends on
# editing the cached QGIS layer.
ROUTE_ORDER = ["r4", "r3", "r5", "r1", "r2"]
ROUTE_TITLE = {key: f"Route {i}" for i, key in enumerate(ROUTE_ORDER, start=1)}


def load_endpoints(key: str) -> dict[str, dict]:
    """start/end points for a route -> {"start": {...}, "end": {...}}.

    Each has lat/lon (rounded) and the point's label. Loops (start == end within
    ~5 m) collapse in the report to a single Start/End row; keep both here so the
    data stays faithful to the source.
    """
    d = json.loads((FT / f"{key}_endpoints.geojson").read_text())
    out = {}
    for ft in d["features"]:
        p = ft["properties"]
        lon, lat = ft["geometry"]["coordinates"]
        out[p["role"]] = {
            "role": p["role"],
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "label": p.get("label"),
        }
    return out


def load_sites() -> dict[int, dict]:
    """Trip POIs keyed by site_no: coordinates from trip_sites.geojson, table
    attributes (perishability / extent / road_dist_m / note) joined from site_data.json
    so the route table matches the main candidate report. POIs absent from site_data.json
    (field-trip-only sites like 124/125) get null attributes -> "—" in the report.
    """
    attrs = json.loads(SITE_DATA.read_text())["sites"]
    d = json.loads((FT / "trip_sites.geojson").read_text())
    out = {}
    for ft in d["features"]:
        p = ft["properties"]
        no = int(p["site_no"])
        lon, lat = ft["geometry"]["coordinates"]
        a = attrs.get(str(no), {})
        out[no] = {
            "site_no": no,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "perishability": a.get("perishability"),
            "extent": a.get("extent"),
            "road_dist_m": a.get("road_dist_m"),
            "note": a.get("note") or None,
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
            "trip": ROUTE_TITLE[key],      # "Route 1".."Route 5" (report page numbering)
            "start": line["start"],
            "end": line["end"],
            "km": line["km"],
            "poi_nos": ROUTE_POIS[key],
            "pois": pois,
            "endpoints": load_endpoints(key),
        })

    OUT.write_text(json.dumps({"routes": routes}, ensure_ascii=False, indent=1))
    n_poi = sum(len(r["pois"]) for r in routes)
    print(f"route_data.json: {len(routes)} routes, {n_poi} POI rows -> {OUT}")


if __name__ == "__main__":
    main()
