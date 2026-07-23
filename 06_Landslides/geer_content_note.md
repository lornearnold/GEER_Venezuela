# Note — what a GEER landslide chapter typically covers

Purpose: compare the working draft's five-bullet "What are we trying to communicate?" list against the
landslide/slope-stability content of three example GEER reconnaissance reports, to see what's standard,
what we're already covering, and what (if anything) is worth adding. Companion to
[lit_review_1999.md](lit_review_1999.md) and [geology_note.md](geology_note.md).

Reports reviewed:
- **Hokkaido (Iburi) 2018** — GEER, §5.0 *Landslides* (landsliding was the dominant hazard; long chapter).
- **Türkiye (Kahramanmaraş) 2023** — GEER-082, Ch. 9 *Landslides and Rock Falls* (deliberately thin;
  landsliding was *less* than predicted — that's the story).
- **Ecuador (Muisne/Pedernales) 2016** — GEER-ATC, §7.6 *Landslides and Rock Falls* (rainfall-primed,
  figure-driven, two case-study sites).

## The recurring content menu

Pooling the three, a GEER landslide chapter is assembled from some subset of these building blocks. Not
every report uses every block — depth scales with how important landsliding was to the event.

1. **Inventory / order-of-magnitude of coseismic landsliding** — counts, total area, sometimes volume.
   (Hokkaido: >3,300 slides / 66.75 km²; Ecuador: >500 slides via before/after satellite; Türkiye:
   deliberately *un*-quantified, framed as "less than forecast.") Usually the chapter's opening move.
2. **Regional geologic / geomorphic context** — the lithology, weathering profile, and slope character
   that set susceptibility. Often leans on a separate geology chapter but restates the landslide-relevant
   parts (Hokkaido's pumice stratigraphy; Ecuador's mudstone + water table; Türkiye's Tepehan formation).
3. **Triggering / conditioning mechanisms** — shaking vs. antecedent rainfall vs. material state. All
   three foreground **antecedent moisture** alongside shaking (very relevant to us given 1999 + a wet coast).
4. **Landslide typology / classification** — shallow vs. deep-seated, translational vs. rotational,
   slides vs. flows vs. rockfall; usually organized by depth/slope-angle class.
5. **Spatial distribution and its controls** — relating where slides concentrate to slope angle,
   aspect/topography, geology, and **ground-motion directionality**. (Directly parallels our Trends section:
   northward + eastward concentration, watershed distribution, aspect rose.)
6. **Performance of predictive models** — comparing observed slides to the **USGS Ground Failure**
   landslide-probability product. Hokkaido devotes a whole subsection (5.5) to critiquing it; Türkiye
   repeatedly notes reality < model. **This is a standard GEER move and we currently don't do it.**
7. **Site-specific case studies** — a few named sites documented in depth with GPS/azimuth-tagged photos,
   sometimes 3D/UAV models and back-analysis. (Ecuador's Loor/Navas; Hokkaido's Yoshino/Horonai;
   Türkiye's Tepehan.) Our "Site observations" section is the stub for this.
8. **Quantitative slope-stability analysis** — closed-form FS + Newmark/Bray-type seismic-displacement
   analysis on a characteristic slide (Türkiye did this for Tepehan). Optional, depends on data in hand.
9. **Hazard implications** — impact on the built environment / lifelines, and residual/compounding hazard
   (loose material staged for future debris flows). Our "Compounding hazard potential" section is this.
10. **Methods** — imagery sources, before/after change detection, field mapping, UAV-SfM/lidar. Sometimes
    its own chapter, sometimes inline.

## How our five bullets map onto that menu

| Our "What are we trying to communicate?" bullet | Standard GEER block(s) | Status in draft |
|---|---|---|
| Local context of landsliding in this region | #2 geologic context, #3 triggering (1999 history) | ✅ Background section — solid, now cited |
| Rough order of magnitude of coseismic landsliding | #1 inventory | ⚠️ Placeholder ("XX slides / XX km²") — the core deliverable, still to fill |
| What we do / don't know about coseismic slope performance | #4 typology, #5 distribution, #8 analysis | ⚠️ Partly in Trends; "what we don't know" is mostly deferred to Opportunities |
| How 1999 precip history + 2026 quake shape current/near-future risk | #3, #9 compounding hazard | ✅ Compounding hazard section — this is our distinctive angle |
| What field opportunities exist | (see below) | ✅ Opportunities section — strong |

**Our five bullets are well-aligned with GEER convention.** The framing is arguably *richer* than the
Türkiye/Ecuador chapters on the risk-evolution angle (bullet 4 — the 1999-depletion / source-reloading
story), which none of the three examples develop. That's a genuine contribution, not padding.

### Gaps / additions worth considering (none mandatory)

- **USGS Ground Failure comparison (#6) — qualitative only, see the provenance section below.** An earlier
  version of this note recommended a full model-performance check. **That recommendation is withdrawn.**
  Every example that grades the USGS product rigorously does so against an *external agency-grade*
  inventory (GSI, BGS), not against its own rapid mapping. Since we are the mappers and our inventory has
  not been QC'd, a validation claim would overreach and is partly circular if the product informed where
  we looked. Note qualitative consistency at most; put the rigorous comparison in future work.
- **Explicit typology sentence (#4).** We assert "small, shallow failures with occasional larger slides."
  One added clause naming the dominant mechanism (shallow debris slides/flows in the residual-soil mantle,
  à la 1999) would match how the examples classify, and ties to [geology_note.md](geology_note.md).
- **Methods transparency (#10).** All three name their imagery/change-detection approach. We should state,
  even briefly, that the inventory came from post-event satellite imagery + field photos and how areas were
  delineated — Table 6.1 covers sources but not method. Supports the order-of-magnitude claim.

## Is it common to explicitly name "opportunities for future data collection"?

**Common but not universal — and its presence tracks the report/author more than the discipline.**

- **Türkiye (GEER-082): YES, explicitly.** A whole chapter, *11.0 Future Studies and Opportunities*, with
  a verbatim subsection **"Landslides and Rock Falls:"**. It lists exactly our kind of items — a named
  slide (Tepehan) flagged as a case study to validate simplified vs. advanced seismic slope-stability
  methods, correlating rockfall with shaking parameters, and using remote sensing to find slides missed in
  remote terrain.
- **Hokkaido: PARTIALLY — embedded, not a standalone section.** No report-wide "future work" heading for
  landslides, but §5.6.1 (Horonai) has an explicit bulleted future-work list ("Several key evaluations are
  believed important…": basal-clay characterization, cross-sections, stability back-analyses) and the
  pointed idea of **comparing slopes that mobilized vs. adjacent ones that didn't** — nearly identical to
  our proposed 1999-vs-2026 soil-depth comparison.
- **Ecuador: NO.** §7.6 ends abruptly on the last site with no forward-looking subsection (any such content
  would sit in the report-wide Conclusions, outside the landslide section).

**Takeaway.** A dedicated "Opportunities for future data collection" section is well within GEER norms —
Türkiye does exactly this, and Hokkaido does it in miniature. Where it appears, it's concrete and
site/method-specific (validate X method on Y slide; go collect Z measurement to test a hypothesis), which
is precisely the register of our current Opportunities section. Keeping ours is defensible and on-genre;
if anything it's a strength. The one stylistic note: the examples tie each opportunity to a specific
scientific question or a named site, which our list already does well (esp. the soil-depth-over-bedrock
and runout-distance items). No change needed there — if anything, the provenance finding below makes the
Opportunities section *more* load-bearing, since that's where the rigorous inventory work belongs.

## How the USGS Ground Failure product is actually used (framing)

Checked directly in the two reports that invoke it. Both use it the same way: **a retrospective
model-check, never as targeting guidance.** Neither says "we used the product to decide where to look."

- **Hokkaido §5.5** is titled *"**Performance Of** The USGS-Ground Failure Predictions"* — the mapped
  inventory is ground truth and the model is the object being graded: *"USGS model predictions
  **misidentified** the exact zones of high landslide occurrence"*; overpredicted along the Shikotsu
  Caldera, while observed slides fell in the model's low/no-probability zones; closes by explaining the
  *"misfit between predicted and observed."*
- **Türkiye** states it in passing, past tense: landslides *"were not as prevalent as was **forecast**
  using USGS shakemap predictions."* Reconnaissance areas are a given (*"in areas where reconnaissance
  was performed"*); the forecast is invoked only afterward as the benchmark reality fell short of.
- Türkiye's Ch. 11 forward-looking items (correlate rockfall with shaking; use remote sensing) are about
  **future work**, and are *not* tied to the USGS product as a targeting tool.

## Provenance and timeline of the example inventories — why we should not claim a model check

| Report | Version | Released | Field recon | Landslide inventory |
|---|---|---|---|---|
| Hokkaido 2018 | **Version 1.0** | Feb 2019 (~5 mo) | Sep 27–Oct 3 (~3 wks) | **Adopted from GSI** (Japan's national mapping agency), from aerial photos collected **Sep 6–11, days 0–5 post-event** |
| Türkiye 2023 | First (no version #) | May 6, 2023 (~3 mo) | Feb 12–Apr 1, phased | **No inventory at all** — a few field-observed sites (Tepehan + scattered rockfalls) |
| Ecuador 2016 | **Version 1** | Oct 14, 2016 (~6 mo) | Apr 26–May 1 (~10–15 d) | **Adopted from BGS** (Pleiades vs. 2013–15 Google Earth differencing) + COE-3 road reports |

**All three are first versions.** None is a follow-up — so the bar we're being compared against is
first-pass reconnaissance, not a refined product.

**The decisive point: none of these teams built its own inventory and then graded a model against it.**

- Where a quantitative inventory exists (Hokkaido, Ecuador), it was **produced by an external official
  body and adopted at face value**. GEER field/UAV work was informal spot-corroboration, not systematic
  verification.
- Where the team relied on its own observations (Türkiye), **no inventory was created**, and a
  remote-sensing inventory was explicitly deferred to future work.
- **No formal QA/QC, ground-truthing, or accuracy assessment of any inventory is described in any of the
  three.** Even Hokkaido — the fullest model-check — hedges its adopted GSI inventory openly: possible
  ~35% undercount (3,307 mapped vs. potentially >5,000 source zones, since coalescing runouts weren't
  discretized) and GEER-observed low-angle slides that GSI missed entirely.

**Implication for §6.2.** The one rigorous model-check in this set grades the USGS product against a
*national mapping agency's* inventory. We have no GSI/BGS equivalent — we are the mappers — so claiming a
validation would assert something none of the three examples actually do from their own mapping. Adopted
approach:

- **(a) Label our inventory preliminary/rapid.** Consistent with a Version-1 reconnaissance report; the
  examples' inventories are rapid products too, ours just isn't agency-produced.
- **(b) Qualitative consistency only** if the USGS product is mentioned — "broadly consistent with"
  rather than a performance grade. Avoids overclaiming and sidesteps circularity if the product informed
  where we looked.
- **(c) Put the rigorous version in future work** — a QC'd inventory plus a formal model comparison.
  This is exactly the Türkiye move and fits our existing Opportunities section.
