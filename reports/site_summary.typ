// GEER Venezuela — example site-summary pages (template lives in template.typ).
// The full priority-ordered packet is report.typ.
// Compile: typst compile reports/site_summary.typ

#import "template.typ": site-page

// --- Page 1: Trocha group — needs 1:6000 to fit (spec 1:1000–1:5000 couldn't
//     hold the 765 m E–W spread on a 7 in figure)
#site-page(
  group: "Trocha",
  fig: "figures/trocha_main_1to6000.png",
  locator: "figures/trocha_locator.png",
  map-scale: 6000,
  bar-meters: 200,
  imagery: [Post-event imagery: Planet Pelican, 0.62 m GSD, 2026-06-26 © 2026 Planet Labs PBC.],
)

// --- Page 2: Site 94 (ungrouped) at 1:2000
#site-page(
  site-nos: (94,),
  fig: "figures/s94_main_1to2000.png",
  locator: "figures/s94_locator_1to100000.png",
  map-scale: 2000,
  bar-meters: 50,
  imagery: [Post-event imagery: Planet Pelican, 0.62 m GSD, 2026-06-26; corner gap filled with Planet SkySat, 0.67 m, 2026-06-27 © 2026 Planet Labs PBC.],
)

// --- Page 3 (ALTERNATIVE for review): Site 94 at 1:3000 — more context,
//     slightly sharper-looking imagery (less magnification of the 0.62 m pixels)
#site-page(
  site-nos: (94,),
  fig: "figures/s94_main_1to3000.png",
  locator: "figures/s94_locator_1to150000.png",
  map-scale: 3000,
  bar-meters: 100,
  imagery: [ALTERNATIVE B — 1:3000. Post-event imagery: Planet Pelican, 0.62 m GSD, 2026-06-26; corner gap filled with Planet SkySat, 0.67 m, 2026-06-27 © 2026 Planet Labs PBC.],
)
