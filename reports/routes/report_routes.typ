// GEER Venezuela — route-map report renderer. Thin by design: it renders whatever
// route_pages.json says. That file is produced by build_route_report.py from route_data.json
// + the route figures manifest. Don't compile directly; drive it through build_route_report.py:
//   uv run python reports/routes/build_route_report.py

#import "template_routes.typ": *

#let build = json("route_pages.json")

#route-packet(units: build.units)
