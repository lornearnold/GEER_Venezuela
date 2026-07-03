# Field reconnaissance priorities — perishable data review

Review of Lorne's draft perishability notes (2026-07-03) against the GEER reconnaissance
manual, the Kaikōura 2016 response literature, and USGS/EERI guidance. Sources at the end;
anything not verified against a fetched source is marked [unverified].

**Event-specific context.** USGS is already running a response page for this event —
*2026 Venezuela Sequence Earthquake-triggered Landslide Hazards* — confirming the M7.2 + M7.5
doublet on June 24, widespread landsliding in the coastal mountains from La Guaira to Naiguatá,
a blocked coastal road between Catia La Mar and Puerto Cruz with isolated communities, and
elevated **multi-year debris-flow risk** to Naiguatá, Caraballeda, Macuto, and Puerto Cruz
(explicitly citing the 1999 Vargas disaster). Their provisional triage grid
(DOI [10.5066/P1MRLOZ7](https://doi.org/10.5066/P1MRLOZ7)) is cached in `data/usgs/` and
feeds the route map in notebook 03.

## Revised perishability ranking

Lorne's three items all survive review, but the list was missing the two most time-critical
categories, and "remote sensing last" conflates *evidence permanence* with *acquisition
urgency*. Revised, most → least perishable:

### 1. Landslide dams / impounded water — hours to days ⚠️ life-safety
Not in the draft notes; belongs above everything. At Kaikōura the Clarence River dam was
spotted on the morning recon flight and had already overtopped and breached by 4 pm the same
day; early identification let authorities warn downstream residents. The evidence itself
perishes: 4 of the 7 highest-risk Kaikōura dams breached in the first significant rainstorms.
Field heuristic worth copying: check drainages wherever flow is absent or discolored.
With the first Caribbean-coast rains, this is also the trigger for the Vargas-style
debris-flow scenario USGS is warning about.

### 2. Debris on transportation corridors before clearing — days
Also missing from the draft. "Removal of debris during recovery operations … quickly obscures
observable significant damage" (Bray et al. 2019). Runout extent over roads, boulder
positions, impact marks, and burial depths on the blocked Catia La Mar–Puerto Cruz road will
be destroyed *by the road-opening effort itself*. One UAV orthomosaic pass per blocked
segment before the bulldozers arrive is the cheapest perishable-data win available. Road-cut,
cut-and-fill, and retaining-wall failures belong here too — they get repaired first.

### 3. Ground cracking near crowns / head scarps — days to first rain
Lorne's #1; holds its top-tier position. Kaikōura's inventory gave cracks their own GIS
feature class (scarps, antiscarps, cracks outside landslide polygons) because they are
"potential sites of water ingress during later rainstorm events" — dual value as perishable
evidence *and* a forward-looking hazard register for reactivation. The safety concern is
echoed in the GEER manual: unstable slopes, loose saturated areas, and block falls are the
principal field hazard for landslide teams. Remote sensing is indeed limited by ground
cover, as noted.

### 4. Timing attribution: witnesses, social media, repeat imagery — days to weeks
Missing from the draft, and unusually important for this event because it was a **doublet**:
attributing a failure to the M7.2, the M7.5, aftershocks, or rain will be impossible later
without eyewitness accounts and time-stamped media. Kaikōura's schema tracks confidence in
"co-seismic occurrence" as an attribute. GEER manual tips: search social media early using
lay terms and local place names (technical vocabulary returns nothing); use pre-event
Street View / imagery to establish what existed before. Memories and media availability
decay fast. [Formal interview protocols: not detailed in fetched sources.]

### 5. Pre-first-rain state of deposits and source areas — weeks, or until the next storm
The acquisition window is perishable even when the product is permanent. The first big rain
will remobilize debris, breach dams, rework runouts, and erase cracks — so post-event/pre-rain
UAV SfM and satellite baselines need to be flown *now*. Same for sampling failed material
(gradation, moisture, source rock character) before reworking: at Kaikōura, material
character controlled dam behavior — permeable greywacke gravel dams piped and breached;
impervious siltstone block-slides held. Early material characterization feeds dam triage
directly. [Specific moisture-sampling protocols: unverified.]

### 6. Rockfall runout evidence — mixed, as noted
Lorne's #2 and his perishability read is right: boulders in fields persist; impact marks and
anything on infrastructure follow item 2's clock. Kaikōura recorded crown point, debris-toe
point, and runout distance as core inventory attributes — capture toe positions before cleanup.

### 7. Remote characterization of failure zones and adjacent slopes — least perishable on the ground, but task it now
Lorne's #3. DEM differencing for volumes, joint sets from point clouds, and documenting
*non-failed* adjacent slopes (GEER doctrine: record good performance too, and avoid collecting
only evidence that fits one mechanism) can happen later — scarps persist. But tasking must
start immediately: at Kaikōura, satellite mapping began within 24 h and a 1,331-landslide
preliminary inventory built in 8 days *guided the field teams' routes*. Also verified: visual
estimates of failure geometry by experienced engineers proved unreliable and highly
conservative — survey (TLS/lidar/SfM), don't eyeball, and repeat surveys to detect ongoing
deformation.

## Capture-method best practices (from the GEER manual v4 unless noted)

- **Photos**: sync camera clock to GPS time (photograph the GPS clock at the start and end of
  each day); always include a scale object; include background scenery so a later team can
  reoccupy the spot; wide-context shot first, then detail; stereo pairs (offset 0.5–several m)
  for 3D; every photo site gets a waypoint; sort photos into waypoint-named folders nightly.
- **Georeferencing**: WGS84, decimal degrees, SI units; GPS track logs on all day (~100 m
  increments driving, 5–20 s walking) — the track log doubles as route documentation and
  reveals coverage gaps. Site IDs = observer initials + sequence number (e.g., LA07).
- **UAV / SfM / lidar** (Bray et al. 2019): SfM is the tool of choice for steep, vegetated, or
  inaccessible terrain; fixed-wing UAV for settlement-scale orthos, quadcopter for site
  detail; repeat terrestrial-lidar scans catch cm-scale ongoing deformation. The NHERI RAPID
  facility loans this instrumentation (Wartman et al. 2020).
- **Inventory schema** worth adopting wholesale (Kaikōura, Dellow et al. 2017): per landslide —
  source polygon, debris polygon, crown point, toe point; a separate line class for cracks;
  attributes for material, movement style, first-time vs reactivated, connectivity to drainage
  (uncoupled/coupled/blocked), mapping method + confidence, originator; explicit "obscured
  area" polygons where clouds blocked mapping.
- **Field operations**: morning task/safety briefing, evening retargeting meeting; one
  dedicated **data manager** merges waypoints, photos, and observations into a daily KML
  pushed to every laptop; know the "end of the road" beyond which you walk; first-aid and
  comms per vehicle.

## Report / product conventions (for the eventual shareable report)

- **Two-stage reporting** (GEER): quick web report within ~2 weeks; comprehensive report
  within ~4–6 weeks. Plan the shareable product around that first deadline.
- **The organizing product is a filterable geographic file** (GEER uses KML): Location,
  Photos, and Observations tables keyed by SiteID, rendered as filterable placemarks. Our
  GeoJSON exports already match this shape; a web map or KML export is the natural
  deliverable format.
- **Route + watch-list precedent is standard practice**: GEER's daily KML is explicitly for
  planning the next day's routes; Kaikōura's 8-day satellite inventory guided field routes.
  Notebook 03's watch-segment map is this pattern — seed it with the USGS grid and grow it
  with the crack/dam registers (items 1 and 3).
- **Archive to DesignSafe with a DOI** when done (the Kaikōura GEER inventory did).
- **Apps**: EERI LFE uses Fulcrum with standard recon forms; StraboSpot is an open NSF
  geologic field app [earthquake-recon use unverified].

## Sources

| Source | What it supports |
|---|---|
| [GEER Manual for Reconnaissance Teams v4 (2014)](https://geerassociation.org/images/GEER_Documents/GEER_Recon_Team_Manual_2014_v4.pdf) | Perishable-data doctrine, photo/GPS protocols, site IDs, data manager, KML product, report timelines |
| [Dellow et al. 2017, Bull. NZSEE 50(2)](https://bulletin.nzsee.org.nz/index.php/bnzsee/article/download/70/56/) | Kaikōura dams (Clarence 16-h breach), dam-triage workflow, inventory schema, crack mapping, TLS repeat surveys |
| [Bray et al. 2019, Frontiers in Built Environment](https://www.frontiersin.org/journals/built-environment/articles/10.3389/fbuil.2019.00005/full) | Debris-removal perishability, satellite timeline, 8-day inventory guiding routes, SfM/UAV/lidar use |
| [USGS 2026 Venezuela Sequence landslide page](https://www.usgs.gov/programs/landslide-hazards/science/2026-venezuela-sequence-earthquake-triggered-landslide-hazards) | Event specifics, corridor closures, debris-flow warnings, triage-grid data |
| [Wartman et al. 2020, Frontiers in Built Environment](https://www.frontiersin.org/journals/built-environment/articles/10.3389/fbuil.2020.573068/full) | Perishable-data definition, RAPID facility, DesignSafe archiving |
| [EERI Learning From Earthquakes](https://learningfromearthquakes.org/activities/reconnaissance/) | Fulcrum forms, virtual clearinghouse, multi-disciplinary deployment model |

**Known gaps** (not covered by verified sources): formal witness-interview protocols;
in-situ moisture sampling procedures; InSAR for post-event slope movement (a Kaikōura
slow-landslide InSAR study exists — Cao et al. 2023, GRL — not yet reviewed).
