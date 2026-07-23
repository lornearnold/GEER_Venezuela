# Literature note — the 1999 Vargas debris-flow disaster

Background for §6.2. Addresses the four items flagged in the working draft: (1) date/description of
the 1999 event, (2) area denuded and debris volume, (3) whether slide-outline maps exist, (4) a
"normal" **background rate of individual small landslides** for this coast — the chronic, low-magnitude
shallow failures visible scattered through the pre-event imagery, *not* the once-a-century
catastrophes. Numbers are cited inline; full references at the bottom.

## 1. Date and description

The disaster occurred **December 14–16, 1999** (the destructive debris flows and flash floods struck
in the early hours of **December 16**), driven by an exceptional rainstorm on the north slope of the
**Cordillera de la Costa**, principally in **Vargas state** north of Caracas (Larsen et al., 2001).

- Rainfall: **293 mm** fell over the first two weeks of December (>5× the average), followed by
  **911 mm on December 14–16** at the Maiquetía airport gauge (Larsen et al., 2001).
- Failures were **thousands of shallow debris flows and soil slips** — a few meters or less deep but
  hundreds of meters long/wide — that mobilized down steep canyons and disgorged onto the coastal
  alluvial fans. A sample of 26 scars had a **mean hillslope angle of 42° (σ = 7.6°)**
  (Larsen et al., 2001).
- Most scars are on the **north side of the range, largely inside El Ávila National Park** (undeveloped
  forest), so most deaths were on the fans below, not in the source areas (Larsen et al., 2001).
- Death toll: estimated **15,000–30,000** (never precisely known); >8,000 residences and ~700 apartment
  buildings damaged or destroyed; economic loss ~$1.79 B (Larsen et al., 2001; USGS FS-103-01).

This is directly relevant to the June 2026 sequence: the same north-facing slopes above
Caracas–Caraballeda that concentrated 1999 activity are where the 2026 coseismic landslides cluster.

## 2. Area denuded and volume of debris — with the correlation

The event drained through **~24 catchments over ~50 km of coast**, with a combined **~200 km²** of
drainage area upstream of the fans (Larsen et al., 2001; López et al.).

**Sediment yield (the "correlation" worth quoting):** for the 1999 storm, sediment yield from that
~200 km² of contributing watershed reached **as much as 100,000 m³/km²** (López et al.). This is the
cleanest area-normalized number in the literature and is the one to pair with our own area estimate.

**Per-fan volumes measured by USGS** (Larsen et al., 2001):

| Fan | Watershed area | Debris-flow / delta volume | Notes |
|-----|----------------|----------------------------|-------|
| Caraballeda (Río San Julián) | (fan of a ~few km²-scale basin) | **~1.25 M m³** deposited on the fan; **~450,000 m³** new subaerial delta | deposits up to **4 m** thick; boulders up to **10 m** long |
| Carmen de Uria | **11.9 km²** | **~233,000 m³** new subaerial delta | implies a **minimum basin-averaged erosion depth of ~20 mm** (a floor, not the true value) |

Whole-event **volume estimates cited elsewhere run ~1.8–2 million m³** for individual major fans / the
best-studied sectors, and the event is ranked among the **largest historically documented
rainfall-induced debris-flow events worldwide** (USGS; secondary sources). Note these are per-fan or
per-sector figures — there is no single tidy "total volume for all of Vargas" number in the primary
literature, so if we report one we should scope it to the fans it covers.

Sediment was disgorged onto fans in quantities up to **15 metric tonnes/m²**; clasts ranged from clay
to **10-m boulders** (Larsen et al., 2001).

## 3. Do slide-outline maps exist?

**Yes, but mostly of the deposits on the fans, not a range-wide scar inventory.**

- **USGS Map I-2772** — Wieczorek et al., *Debris-flow and flooding deposits in coastal Venezuela
  associated with the storm of December 14–16, 1999.* This is the published map product with mapped
  **deposit boundaries** on the affected fans (Caraballeda / Los Corales, San Julián, Carmen de Uria,
  etc.). This is the closest thing to the "outlines" Patricia wants, and it is a USGS pub, so figures
  should be reproducible with attribution.
- **USGS OFR 01-0144** — Wieczorek et al., debris-flow and flooding hazard assessment with mitigation
  discussion (companion open-file report).
- The **source-area scar inventory** (the hillslope failures inside El Ávila) is less consistently
  published as a single GIS layer; Larsen et al. worked from 1994-vs-2000 aerial photo pairs
  (e.g. their Fig. 2, Boca del Uria) rather than a complete digitized scar inventory. **This is exactly
  the gap the draft notes** — our own outlines from pre-event imagery near the coast would complement,
  not duplicate, the published deposit maps, and would extend coverage upslope where they stop.

**Action:** pull I-2772 and OFR 01-0144 to see how far east/west their mapped outlines extend, then
digitize only the gaps from our imagery.

## 4. "Normal" background rate of individual small landslides

This is the question the pre-event imagery raises: scattered shallow failures are everywhere on these
slopes, so what is the *baseline* rate independent of any one storm or earthquake? There is **no
published rate for the Cordillera de la Costa specifically**, but the humid-tropical-mountain
literature gives a well-established metric and a strong regional analog (Puerto Rico — same
humid-tropical Caribbean mountain setting, and studied by Larsen, who also worked Vargas).

The right metric is not "events per century" but **how much of the landscape turns over per year via
small failures** — usually expressed as:

- **Landslide mobilization rate (LMR)** — vertical lowering equivalent, in **mm/yr**.
- **Fraction of landscape disturbed per year** (%/yr), and its inverse, **hillslope turnover time**.
- **Landslide density** — failures per km² (for a given inventory/time window).

**Benchmark numbers:**

- **Eastern Puerto Rico (best analog):** background landsliding affects **~0.011% of the landscape per
  year**, i.e. a mean **hillslope turnover time of ~1,320 years** (Larsen & Torres-Sánchez, 1992;
  Larsen & Torres-Sánchez, 1998). Landslide-producing storms recur **~1.2×/yr**, each producing tens
  to hundreds of individual slides; mean annual rainfall ~2,000+ mm. This is the cleanest "normal rate"
  figure to cite as an analog.
- **Tropical Andes (humidity gradient):** landslide mobilization rates of **~2 mm/yr** in natural
  forest rising to **~5 mm/yr** in human-disturbed terrain (Restrepo & others / Vanacker-type work,
  ScienceDirect). Confirms the rate is (a) chronic and non-trivial and (b) sensitive to land use.
- **Density, for scale:** reported shallow-landslide densities in tropical mountains span
  **~0.08 to ~35 slides/km²** depending on setting and trigger (e.g. >900 shallow slides over 27 km²
  ≈ 35/km² at Miravalles, Costa Rica). Wide range — density is trigger- and inventory-dependent, so
  it's best used for our *own* mapped area, not as an imported baseline.

**Why the rate is high here even in "quiet" years** — the same drivers that made 1999 catastrophic
also sustain chronic failure: steep tectonically active fronts (**uplift ~2–5 mm/yr**), ~50
thunderstorms/yr, and thin colluvial soils on ~40° slopes. Colluvium-supply-limited models
(Nature *Sci. Rep.* 2016) show that between big events, slopes reaccumulate loose material — which is
the mechanism behind the draft's testable hypothesis that **1999 depleted source material** and the
chronic small slides are (partly) the system reloading.

**How to use this in §6.2:** frame our pre-event imagery slides as the *background signal* and estimate
a local rate the same way the analog studies do — count failures in a defined pre-event area, divide by
area and by the imagery time span, and compare against the Puerto Rico **~0.01%/yr / ~1,300-yr turnover**
benchmark. Then the 2026 coseismic slides can be reported as a multiple of that background.

---

## References

- **Larsen, M.C., Wieczorek, G.F., Eaton, L.S., Torres-Sierra, H., 2001.** *The rainfall-triggered
  landslide and flash-flood disaster in northern Venezuela, December 1999.* Proc. 7th Federal
  Interagency Sedimentation Conf., Reno, NV, p. IV-9–IV-16.
  https://stri-sites.si.edu/docs/publications/pdfs/Larsen-etal-FISC-2001.pdf  ← **primary source, read in full**
- **Wieczorek, G.F., et al.** *Debris-flow and flooding deposits in coastal Venezuela associated with
  the storm of December 14–16, 1999.* USGS Miscellaneous Investigations **Map I-2772**.
  https://pubs.usgs.gov/publication/i2772  ← **mapped deposit outlines**
- **Wieczorek, G.F., et al., 2001.** *Debris-flow and flooding hazards … with a discussion of
  mitigation options.* USGS **Open-File Report 01-0144.** https://pubs.usgs.gov/of/2001/ofr-01-0144/
- **USGS Fact Sheet FS-103-01.** *The Venezuela debris flow and flash flood disaster of 1999.*
  https://pubs.usgs.gov/fs/fs-0103-01/fs-0103-01.pdf
- **López, J.L., et al.** (cited for sediment-yield ~100,000 m³/km² over ~200 km²; see IWRA congress
  paper, "An integrated approach for debris-flow risk mitigation …").
  https://iwra.org/proceedings/congress/resource/abs912_article.pdf
- **Britannica**, *Venezuela mud slides of 1999* (secondary overview).
  https://www.britannica.com/event/Venezuela-mud-slides-of-1999

**Background-rate sources (§4):**

- **Larsen, M.C. & Torres-Sánchez, A.J., 1992 / 1998.** *The frequency and distribution of recent
  landslides in three montane tropical regions of Puerto Rico.* Geomorphology 24, 309–331.
  https://fs.usda.gov/treesearch/pubs/30313 — source of the **~0.011%/yr disturbed, ~1,320-yr
  turnover** benchmark. **Best regional analog.**
- **Landslide process rates along a humidity gradient, tropical Andes** (Restrepo/Vanacker-type),
  Geomorphology. LMR **~2 mm/yr (natural) → ~5 mm/yr (disturbed)**.
  https://www.sciencedirect.com/science/article/abs/pii/S0169555X11005551
- **Colluvium supply limits storm-triggered landslide frequency in humid regions**, *Sci. Rep.* 6,
  34438 (2016). https://www.nature.com/articles/srep34438 — mechanism for slope "reloading" between
  events.

### Confidence flags

- **Solid (primary, USGS):** all Larsen et al. (2001) per-fan volumes, rainfall, dates, hillslope
  angles.
- **Solid but scope-limited:** sediment yield 100,000 m³/km² and the ~200 km² / ~24-stream figures —
  from López et al.; good numbers but confirm exact wording against the source PDF before quoting.
- **Use with care:** the "1.8–2 million m³" whole-event volume — appears in secondary sources and
  applies to major fans/sectors, not a rigorously summed range-wide total. Scope any total we report.
- **Analog, not local (§4):** the ~0.01%/yr / ~1,300-yr background rate is **Puerto Rico**, not the
  Cordillera de la Costa — cite it as a comparator, and derive our own local rate from the pre-event
  imagery. No Cordillera-de-la-Costa-specific background rate was found in the search.
- **Gap:** no single published range-wide *scar* inventory GIS layer found — confirms the draft's plan
  to digitize source-area outlines ourselves is worthwhile.
