// GEER Venezuela — shared template for one-page site summaries.
// Imported by report.typ (the full packet) and site_summary.typ (examples).
//
// Table content is NOT typed here — it comes from site_data.json, generated from the
// QGIS candidates layer by:  uv run python reports/export_site_data.py
// Pages reference sites by group name (or explicit site numbers) only.

// ================================================== adjustable layout knobs ===

// --- fonts & text sizes
#let font-family = "Arial"
#let size-body = 9pt          // table text
#let size-title = 11pt        // header page title
#let size-header = 9pt        // header secondary text
#let size-caption = 8pt
#let size-notes-col = 8.5pt   // table Notes column
#let size-footnote = 7.5pt
#let size-scalebar = 6pt

// --- page geometry
// NOTE: the header is drawn INSIDE the top margin (see comment at `header:` below),
// so margin-top must be at least header height + header-gap.
#let margin-x = 0.6in
#let margin-top = 1.05in
#let margin-bottom = 0.5in
#let header-gap = 0.18in      // gap between header rule and body (Typst "header-ascent")

// --- figure & overlays
#let fig-border = 0.6pt       // main figure frame weight
#let inset-width = 1.55in     // locator inset size on page
#let inset-frame = 1.4pt      // white frame around inset
#let overlay-pad = 6pt        // inset / scale bar / north arrow offset from figure edge
#let scalebar-height = 2.5pt
#let caption-gap = 6pt        // between figure and table
#let footnote-gap = 4pt       // between table and footnote

// --- table
#let table-columns = (0.55fr, 1.0fr, 0.8fr, 1.9fr, 1.1fr, 2.4fr)
#let table-inset = 5pt
#let table-header-rule = 0.8pt
#let table-row-rule = 0.4pt
#let table-header-fill = luma(240)

// --- colors
#let link-color = rgb("#1a56b0")
#let muted = luma(80)
#let footnote-color = luma(100)

// --- locator inset scale = locator-mult × main figure scale
//     (render the inset PNGs from QGIS at this scale — see PROGRESS.md)
#let locator-mult = 50

// ================================================================ site data ===

#let site-data = json("site_data.json")

// All site numbers in a group, ascending
#let sites-in-group(g) = (
  site-data.sites.pairs()
    .filter(p => p.at(1).group == g)
    .map(p => int(p.at(0)))
    .sorted()
)

// include a linebreak-tolerant Google Maps link for a lat/lon
#let fmt-dd(v) = {
  let a = calc.abs(v)
  let whole = calc.trunc(a)
  let frac = str(calc.round((a - whole) * 1000000))
  while frac.len() < 6 { frac = "0" + frac }
  str(whole) + "." + frac
}
// ASCII decimal string for URLs — Typst's str() renders negative numbers with a
// Unicode minus sign (U+2212), which Google Maps cannot parse; force "-".
#let url-dd(v) = if v < 0 { "-" + str(calc.abs(v)) } else { str(v) }
#let coord-link(lat, lon) = link(
  "https://www.google.com/maps/search/?api=1&query=" + url-dd(lat) + "%2C" + url-dd(lon),
)[#fmt-dd(lat)°N, #fmt-dd(lon)°W]

// 300000 -> "300,000" for captions
#let fmt-thousands(n) = {
  let s = str(n)
  let out = ""
  let i = 0
  for c in s.rev() {
    if i != 0 and calc.rem(i, 3) == 0 { out = "," + out }
    out = c + out
    i += 1
  }
  out
}

// ------------------------------------------------------------------ helpers ---

#let scalebar(scale, meters) = {
  let bar-w = 1000mm * meters / scale
  let half = bar-w / 2
  box(fill: white, inset: 3pt, radius: 1pt, stroke: 0.4pt + gray)[
    #stack(
      dir: ttb,
      spacing: 1.5pt,
      stack(
        dir: ltr,
        box(width: half, height: scalebar-height, fill: black, stroke: 0.4pt + black),
        box(width: half, height: scalebar-height, fill: white, stroke: 0.4pt + black),
      ),
      text(size: size-scalebar)[0 #h(half - 12pt) #str(int(meters / 2)) #h(half - 16pt) #str(int(meters)) m],
    )
  ]
}

#let north-arrow = box(fill: white, inset: 2.5pt, radius: 1pt, stroke: 0.4pt + gray,
  text(size: 8pt, weight: "bold")[N #text(size: 7pt)[▲]])

// -------------------------------------------------------------- page layout ---

#let site-page(
  group: none,          // group name (auto-selects its sites), or none
  site-nos: none,       // explicit site numbers — required when group is none
  title: none,          // header title override (e.g. bundled pages)
  fig: "",              // main map image path
  locator: "",          // locator inset image path
  map-scale: 6000,      // 1:N
  locator-scale: none,  // inset 1:N — defaults to map-scale × locator-mult
  bar-meters: 200,      // scale bar ground length
  imagery: "",          // imagery credit line
) = {
  let nos = if site-nos != none { site-nos } else { sites-in-group(group) }
  let n = nos.len()
  let loc-scale = if locator-scale != none { locator-scale } else { map-scale * locator-mult }

  page(
    paper: "us-letter",
    margin: (x: margin-x, top: margin-top, bottom: margin-bottom),
    header-ascent: header-gap,
    // The header block is laid out INSIDE the top margin: it occupies the strip
    // between the paper edge and (body start − header-ascent). If its content is
    // taller than that strip it overflows toward the paper edge — which is what
    // happened with the earlier 0.55 in top margin.
    header: context [
      #set text(font: font-family, size: size-header)
      #grid(
        columns: (1fr, auto),
        align: (left + bottom, right + bottom),
        [
          #text(weight: "bold", size: size-title)[
            #if title != none [#title] else if group != none [Site group: #group] else [Site #nos.at(0) (ungrouped)]
          ] \
          #text(fill: muted)[Candidates for landslide reconnaissance (#n #if n == 1 [site] else [sites])]
        ],
        [
          GEER (landslides team) 2026-06-24 Venezuela Earthquakes \
          #text(fill: muted)[Draft · #datetime.today().display("[year]-[month]-[day]")]
        ],
      )
      #v(-4pt)
      #line(length: 100%, stroke: 0.6pt + luma(120))
    ],
  )[
    #set text(font: font-family, size: size-body)
    #show link: it => underline(stroke: 0.4pt + link-color, text(fill: link-color, it))

    // ------- figure: main map with locator inset + scale bar + north arrow
    #figure(
      box(stroke: fig-border + luma(60), clip: true)[
        #image(fig, width: 100%)
        #place(top + right, dx: -overlay-pad, dy: overlay-pad,
          box(stroke: inset-frame + white, image(locator, width: inset-width)))
        #place(bottom + left, dx: overlay-pad, dy: -overlay-pad, scalebar(map-scale, bar-meters))
        #place(top + left, dx: overlay-pad, dy: overlay-pad, north-arrow)
      ],
      caption: [
        #set text(size: size-caption)
        #set align(left)
        Candidate site#if n > 1 [s] at 1:#fmt-thousands(map-scale).
        Inset: setting at 1:#fmt-thousands(loc-scale) (basemap © Google);
        red box = figure extent. #imagery
      ],
      supplement: none,
      numbering: none,
    )

    #v(caption-gap)

    // ------- site table (rows pulled from site_data.json by site number)

    #table(
      columns: table-columns,
      align: (center, center, center, center, center, left),
      stroke: (x, y) => if y == 0 { (bottom: table-header-rule + black) } else { (bottom: table-row-rule + luma(200)) },
      fill: (x, y) => if y == 0 { table-header-fill },
      inset: table-inset,
      table.header(
        [*Site*], [*Perishability estimate*], [*Extent estimate*], [*Coordinates (WGS84)*], [*Approx. dist. to road (m)*], [*Notes*],
      ),
      ..for no in nos {
        let s = site-data.sites.at(str(no))
        (
          [*#no*], s.perishability, s.extent,
          coord-link(s.lat, s.lon),
          str(s.road_dist_m),
          text(size: size-notes-col, s.note),
        )
      },
    )

    #v(footnote-gap)
    #text(size: size-footnote, fill: footnote-color)[
      - Perishability estimate indicates priorty for documenting evidence before it degrades or is removed.
      - Approx. dist. to road: straight-line distance to nearest drivable road in open street map.
      - All sites flagged from available pre- and post-event satellite imagery; field verification required.
    ]
  ]
}
