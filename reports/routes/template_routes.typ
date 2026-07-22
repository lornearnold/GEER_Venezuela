// GEER Venezuela — route-map report template (one page per field-trip route).
//
// A sibling of ../template.typ (candidate-site packet). It reuses that file's layout
// knobs, helpers (scalebar, north-arrow, coord-link, fmt-thousands, colors, fonts) via
// import, and adds a route-page layout: a route map (route line + its points of interest,
// Google roadmap base, locator inset) over a table of the route's POIs.
//
// Content comes from route_data.json (built by build_route_data.py from the field-trip
// GeoJSONs) and per-route figures listed in route_pages.json (built by build_route_report.py).
// Figures are rendered from QGIS with the route's start/end point LABELS removed.

#import "../template.typ": (
  font-family, size-body, size-title, size-header, size-caption, size-notes-col,
  size-footnote, size-scalebar,
  margin-x, margin-top, margin-bottom, header-gap,
  fig-border, inset-width, inset-frame, overlay-pad, caption-gap, footnote-gap,
  table-inset, table-header-rule, table-row-rule, table-header-fill,
  link-color, muted, footnote-color, locator-mult,
  scalebar, north-arrow, fmt-thousands, coord-link,
)

#let route-data = json("route_data.json")

// slope/aspect may be null in the source; render an em dash instead of "none".
// Numbers must be turned into content for table cells — str() them.
#let or-dash(v) = if v == none { [—] } else if type(v) == float or type(v) == int { str(v) } else { v }

// ------------------------------------------------------------- route page ---

#let route-page(
  route,                 // a route dict from route_data.json
  fig: "",               // main route-map image path
  locator: "",           // locator inset image path
  map-scale: 40000,      // 1:N of the main map
  locator-scale: none,   // inset 1:N — defaults to map-scale × locator-mult
  bar-meters: 1000,      // scale bar ground length
  basemap-credit: [© Google],
) = {
  let pois = route.pois
  let n = pois.len()
  let loc-scale = if locator-scale != none { locator-scale } else { map-scale * locator-mult }

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

    // ------- route map: line + POIs with locator inset + scale bar + north arrow
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
        #route.trip at 1:#fmt-thousands(map-scale). Blue line = drivable route
        (#route.km km); numbered dots = points of interest.
        Inset: setting at 1:#fmt-thousands(loc-scale) (basemap #basemap-credit);
        red box = figure extent. Basemap © Google.
      ],
      supplement: none,
      numbering: none,
    )

    #v(caption-gap)

    // ------- POI table (this route's points of interest, in visit order)
    #table(
      columns: (0.7fr, 1.9fr, 1.0fr, 0.9fr, 0.9fr),
      align: (center, center, center, center, center),
      stroke: (x, y) => if y == 0 { (bottom: table-header-rule + black) } else { (bottom: table-row-rule + luma(200)) },
      fill: (x, y) => if y == 0 { table-header-fill },
      inset: table-inset,
      table.header(
        [*Site*], [*Coordinates (WGS84)*], [*Setting*], [*Slope (°)*], [*Aspect*],
      ),
      ..for s in pois {
        (
          [*#s.site_no*],
          coord-link(s.lat, s.lon),
          or-dash(s.location),
          or-dash(s.slope_deg),
          or-dash(s.aspect_dir),
        )
      },
    )

    #v(footnote-gap)
    #text(size: size-footnote, fill: footnote-color)[
      - Points of interest are landslide candidate sites; route routed to pass as close as
        drivable roads allow (OpenStreetMap).
      - Setting / slope / aspect from the candidate-site attributes; "—" where not recorded.
      - Start and end points are shown on the map without labels; see the header for the
        route's start → end description.
    ]
  ]
}

// ==================================================================== packet ===

// units: array of route-page arg dicts, each { key, fig, locator, map_scale, ... }.
// Each unit's `key` selects its route from route_data.json.
#let route-packet(units: ()) = {
  let by-key = (:)
  for r in route-data.routes { by-key.insert(r.key, r) }
  for u in units {
    let route = by-key.at(u.key)
    route-page(
      route,
      fig: u.fig,
      locator: u.locator,
      map-scale: u.map_scale,
      locator-scale: u.at("locator_scale", default: none),
      bar-meters: u.bar_m,
    )
  }
}
