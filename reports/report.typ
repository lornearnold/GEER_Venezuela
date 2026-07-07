// GEER Venezuela — report renderer. Thin by design: it renders whatever
// reports/build/pages.json says. That file (page list, cover on/off, supplement
// badge) is produced by build_report.py from the candidate attributes + the
// figures manifest — there is no hand-maintained plan and this file has no config.
//
// Don't compile this directly; drive it through build_report.py (or /geer-report):
//   uv run python reports/build_report.py --mode full
//   uv run python reports/build_report.py --mode supplement --sites 111-123

#import "template.typ": *

#let build = json("build/pages.json")

#packet(
  doc-label: build.doc_label,   // string badge, or none
  cover: build.cover,           // cover dict, or none
  units: build.units.map(u => (
    title: u.title,
    site-nos: u.site_nos,
    fig: u.fig,
    locator: u.locator,
    map-scale: u.map_scale,
    locator-scale: u.locator_scale,
    bar-meters: u.bar_m,
    imagery: u.imagery,
  )),
)
