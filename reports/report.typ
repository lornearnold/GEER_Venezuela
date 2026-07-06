// GEER Venezuela — candidate landslide site packet for field teams.
// Cover page + one summary page per unit, in approximate priority order:
//   2) high perishability, populated   3) med perishability, populated (extent desc)
//   4) med perishability, remote (extent desc)   5) everything else
//   6) ungrouped low-confidence sites (bundled as one group)
//
// Page order, figures, scales, and imagery picks come from report_plan.json,
// built from the QGIS project (see PROGRESS.md). Site attributes come from
// site_data.json (uv run python reports/export_site_data.py).
//
// Compile: typst compile reports/report.typ

#import "template.typ": *

#let plan = json("report_plan.json")

// ------------------------------------------------------------- cover page ---

#let cover-map-width = 5.9in
#let cover-notes-size = 8pt

#page(
  paper: "us-letter",
  margin: (x: margin-x, top: 0.65in, bottom: margin-bottom),
)[
  #set text(font: font-family, size: size-body)

  #align(center)[
    #text(size: 15pt, weight: "bold")[GEER — 2026-06-24 Venezuela Earthquakes]
    #v(1pt)
    #text(size: 11pt)[Landslide reconnaissance — candidate site packet (landslides team)]
    #v(0pt)
    #text(size: 9pt, fill: muted)[Draft · #datetime.today().display("[year]-[month]-[day]")]
  ]

  #v(4pt)

  // --- coverage map
  #figure(
    box(stroke: fig-border + luma(60), clip: true, image(plan.cover.fig, width: cover-map-width)),
    caption: [
      #set text(size: size-caption)
      #set align(left)
      Coverage reviewed, 1:#fmt-thousands(plan.cover.scale). Yellow dots = candidate sites;
      blue outlines = post-event imagery footprints containing at least one site;
      red dashed area = dead zone (no post-event imagery reviewed to date).
      Basemap © Google.
    ],
    supplement: none,
    numbering: none,
  )

  #v(6pt)

  // --- imagery sources
  #text(weight: "bold")[Imagery reviewed]
  #v(2pt)
  #table(
    columns: (3.4fr, 1.1fr, 1.3fr, 0.9fr),
    align: (left, center, center, center),
    stroke: (x, y) => if y == 0 { (bottom: table-header-rule + black) } else { (bottom: table-row-rule + luma(200)) },
    fill: (x, y) => if y == 0 { table-header-fill },
    inset: 4pt,
    table.header([*Source*], [*GSD (m)*], [*Acquired*], [*Scenes*]),
    ..for r in plan.cover.source_rows {
      (r.source, r.gsd_m, r.date, str(r.scenes))
    },
  )

  #v(6pt)

  // --- notes
  #text(weight: "bold")[Notes]
  #v(2pt)
  #set text(size: cover-notes-size)
  - The potential landslide sites in this document are listed in approximate priority order.
  - Local expertise should take precedence over the sites indicated in this package. If perishable
    evidence of landslide activity exists elsewhere, that is of interest. If some of the sites
    flagged as potential landslides are actually caused by some other source (e.g., land clearing),
    cross them off the list. However, there are some sites with apparent landslides in areas with
    mining activity that may still be valuable to collect data on.
  - Notes with "head scarp" indicate that mapping crack size, density, and orientation behind the
    potential landslide is of interest.
  - A dead zone (no post-event imagery reviewed to date) exists in an area where high landslide
    concentration is expected, but little built infrastructure is apparent.
  - Sites with "low confidence" in the notes were initially tagged as potential landslides, but
    have suspected anthropogenic causes.
]

// ----------------------------------------------------------- site pages ---

#for u in plan.units {
  site-page(
    title: u.title,
    site-nos: u.site_nos,
    fig: u.fig,
    locator: u.locator,
    map-scale: u.scale,
    locator-scale: u.locator_scale,
    bar-meters: u.bar_m,
    imagery: u.credit,
  )
}
