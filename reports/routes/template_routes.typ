// GEER Venezuela — route-map report template (one page per field-trip route).
//
// A sibling of ../template.typ (candidate-site packet). It reuses that file's layout
// knobs, helpers (scalebar, north-arrow, coord-link, fmt-thousands, colors, fonts) via
// import, and adds a route-page layout: a route map (route line + its start/end points
// and points of interest, Google roadmap base) over a table of the route's start, end,
// and POIs.
//
// Content comes from route_data.json (built by build_route_data.py from the field-trip
// GeoJSONs) and per-route figures listed in route_pages.json (built by build_route_report.py).
// The map extent is fit to the whole route line; POI labels are offset off their dots.

#import "../template.typ": (
  font-family, size-body, size-title, size-header, size-caption, size-notes-col,
  size-footnote, size-scalebar,
  margin-x, margin-top, margin-bottom, header-gap,
  fig-border, overlay-pad, caption-gap, footnote-gap,
  table-columns, table-inset, table-header-rule, table-row-rule, table-header-fill,
  link-color, muted, footnote-color,
  scalebar, north-arrow, fmt-thousands, coord-link,
)

#let route-data = json("route_data.json")

// A null source field renders as an empty cell (not a placeholder).
// Numbers must be turned into content for table cells — str() them.
#let cell(v) = if v == none { [] } else if type(v) == float or type(v) == int { str(v) } else { v }

// Endpoint glyphs — match the map symbols: start = green circle, end = red square.
#let start-color = rgb("#28b43c")
#let end-color = rgb("#d62828")
#let start-glyph = box(circle(radius: 3.2pt, fill: start-color, stroke: 0.5pt + white), baseline: 1pt)
#let end-glyph = box(rect(width: 6pt, height: 6pt, fill: end-color, stroke: 0.5pt + white), baseline: 1pt)

// ------------------------------------------------------------- route page ---

#let route-page(
  route,                 // a route dict from route_data.json
  fig: "",               // main route-map image path
  map-scale: 40000,      // 1:N of the main map
  bar-meters: 1000,      // scale bar ground length
) = {
  let pois = route.pois
  let n = pois.len()
  let ep = route.endpoints
  // A loop (start point == end point within ~5 m) collapses to one Start / End row.
  let is-loop = calc.abs(ep.start.lat - ep.end.lat) < 0.00005 and calc.abs(ep.start.lon - ep.end.lon) < 0.00005

  page(
    paper: "us-letter",
    margin: (x: margin-x, top: margin-top, bottom: margin-bottom),
    header-ascent: header-gap,
    header: context [
      #set text(font: font-family, size: size-header)
      #grid(
        columns: (1fr, auto),
        align: (left + bottom, right + bottom),
        [
          #text(weight: "bold", size: size-title)[#route.trip] \
          #text(fill: muted)[
            Field-trip route · #route.km km · #route.start → #route.end
            (#n #if n == 1 [stop] else [stops])
          ]
        ],
        [
          #text(weight: "bold")[Route map] \
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

    // ------- route map: full route line + start/end + POIs, scale bar, north arrow
    #figure(
      box(stroke: fig-border + luma(60), clip: true)[
        #image(fig, width: 100%)
        #place(bottom + left, dx: overlay-pad, dy: -overlay-pad, scalebar(map-scale, bar-meters))
        #place(top + left, dx: overlay-pad, dy: overlay-pad, north-arrow)
      ],
      caption: [
        #set text(size: size-caption)
        #set align(left)
        #route.trip at 1:#fmt-thousands(map-scale). Blue line = drivable route
        (#route.km km); #start-glyph start, #end-glyph end, numbered dots = points of
        interest. Extent covers the whole route. Basemap © Google.
      ],
      supplement: none,
      numbering: none,
    )

    #v(caption-gap)

    // ------- table: start, points of interest (visit order), end.
    // Endpoint rows carry only the glyph + coordinates; endpoints have no candidate-site
    // attributes, so those cells stay blank (place names are in the page header).
    #let endpoint-row(glyph, e) = (
      align(center)[#glyph],
      [], [],
      coord-link(e.lat, e.lon),
      [], [],
    )
    #table(
      columns: table-columns,
      align: (center, center, center, center, center, left),
      stroke: (x, y) => if y == 0 { (bottom: table-header-rule + black) } else { (bottom: table-row-rule + luma(200)) },
      fill: (x, y) => if y == 0 { table-header-fill },
      inset: table-inset,
      table.header(
        [*Site*], [*Perishability estimate*], [*Extent estimate*], [*Coordinates (WGS84)*], [*Approx. dist. to road (m)*], [*Notes*],
      ),
      ..if is-loop {
        endpoint-row([#start-glyph#h(2pt)#end-glyph], ep.start)
      } else {
        endpoint-row(start-glyph, ep.start)
      },
      ..for s in pois {
        (
          [*#s.site_no*],
          cell(s.perishability),
          cell(s.extent),
          coord-link(s.lat, s.lon),
          cell(s.road_dist_m),
          text(size: size-notes-col, cell(s.note)),
        )
      },
      ..if not is-loop { endpoint-row(end-glyph, ep.end) } else { () },
    )

    #v(footnote-gap)
    #text(size: size-footnote, fill: footnote-color)[
      - #start-glyph~/~#end-glyph mark the route's driving start / end (green circle / red
        square on the map); numbered dots are landslide candidate sites the route is routed
        to pass as close as drivable roads allow (OpenStreetMap).
      - Perishability estimate indicates priority for documenting evidence before it degrades or is removed.
      - Approx. dist. to road: straight-line distance to nearest drivable road in OpenStreetMap.
    ]
  ]
}

// ==================================================================== packet ===

// units: array of route-page arg dicts, each { key, fig, map_scale, bar_m }.
// Each unit's `key` selects its route from route_data.json.
#let route-packet(units: ()) = {
  let by-key = (:)
  for r in route-data.routes { by-key.insert(r.key, r) }
  for u in units {
    let route = by-key.at(u.key)
    route-page(
      route,
      fig: u.fig,
      map-scale: u.map_scale,
      bar-meters: u.bar_m,
    )
  }
}
