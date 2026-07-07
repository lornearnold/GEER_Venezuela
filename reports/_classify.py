"""Shared, deterministic classification of candidate sites into report units.

The report and the KMZ both import this so their section/group/priority logic
can never drift. Everything here is derived from the candidate-site *attributes*
(perishability, location, group, note) — there is no separate hand-maintained
"plan". Rendering metadata (scale, chosen imagery, figure paths) is NOT decided
here; it lives in reports/figures/manifest.json, produced by the /geer-report
render step.

Priority sections (lower number = higher field priority):
    2  high perishability, populated
    3  med  perishability, populated
    4  med  perishability, remote
    5  everything else (high+remote, low+*, …)
    6  ungrouped low-confidence sites (bundled onto one page)

A *unit* is one report page: a named group, a single ungrouped site, or the
one section-6 bundle. A group takes the best (lowest) section any member earns.
"""

from __future__ import annotations

from pathlib import Path
import json

SECTION_NAMES = {
    2: "Priority 1 — high perishability (populated)",
    3: "Priority 2 — medium perishability (populated)",
    4: "Priority 3 — medium perishability (remote)",
    5: "Priority 4 — other sites",
    6: "Priority 5 — ungrouped low-confidence sites",
}

BUNDLE_KEY = "bundle"
BUNDLE_TITLE = "Ungrouped low-confidence sites"


def _norm(v) -> str:
    return (v or "").strip().lower()


def single_section(perish: str, loc: str) -> int:
    """Priority section for one site from its perishability + location."""
    p, l = _norm(perish), _norm(loc)
    if p == "high" and l == "populated":
        return 2
    if p == "med" and l == "populated":
        return 3
    if p == "med" and l == "remote":
        return 4
    return 5  # high+remote, low+anything, or anything unclassified


def is_low_confidence(site: dict) -> bool:
    return "low confidence" in _norm(site.get("note"))


def in_bundle(site: dict) -> bool:
    """Section-6 bundle = ungrouped AND flagged low-confidence in its note."""
    return not (site.get("group") or "").strip() and is_low_confidence(site)


def build_units(sites: dict[str, dict], selection: set[int] | None = None) -> list[dict]:
    """Return report units (pages) in priority order, derived from attributes.

    sites: the {str(site_no): attrs} map from site_data.json.
    selection: keep only units touching these site numbers (None = all). A group
      is kept whole if any member is selected, so adding a site to a group
      re-includes the whole group.

    Each unit: {key, kind ('group'|'site'|'bundle'), section, title, site_nos}.
    """
    groups: dict[str, list[int]] = {}
    singles: list[int] = []
    bundle: list[int] = []

    for k, s in sites.items():
        no = int(k)
        g = (s.get("group") or "").strip()
        if g:
            groups.setdefault(g, []).append(no)
        elif in_bundle(s):
            bundle.append(no)
        else:
            singles.append(no)

    units: list[dict] = []

    for g, members in groups.items():
        members = sorted(members)
        section = min(single_section(sites[str(n)]["perishability"], sites[str(n)]["location"])
                      for n in members)
        units.append({"key": g, "kind": "group", "section": section,
                      "title": f"Site group: {g}", "site_nos": members})

    for no in singles:
        s = sites[str(no)]
        units.append({"key": str(no), "kind": "site",
                      "section": single_section(s["perishability"], s["location"]),
                      "title": f"Site {no} (ungrouped)", "site_nos": [no]})

    if bundle:
        units.append({"key": BUNDLE_KEY, "kind": "bundle", "section": 6,
                      "title": BUNDLE_TITLE, "site_nos": sorted(bundle)})

    # deterministic order: section, then groups before singles, then by first site_no
    kind_rank = {"group": 0, "site": 1, "bundle": 2}
    units.sort(key=lambda u: (u["section"], kind_rank[u["kind"]], u["site_nos"][0]))
    for i, u in enumerate(units):
        u["order"] = i

    if selection is not None:
        units = [u for u in units if selection.intersection(u["site_nos"])]

    return units


def parse_selection(spec: str | None, sites: dict[str, dict]) -> set[int] | None:
    """Parse 'all' | '111-123' | '3,4,94' | '1-9,15' into a set of site numbers."""
    if spec is None or spec.strip().lower() == "all":
        return None
    out: set[int] = set()
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return {n for n in out if str(n) in sites}


if __name__ == "__main__":
    # Self-check: print the derived units (section, kind, key, size).
    here = Path(__file__).resolve().parent
    sites = json.loads((here / "site_data.json").read_text())["sites"]
    units = build_units(sites)
    print(f"{len(units)} units from {len(sites)} sites\n")
    for u in units:
        print(f"  sec{u['section']} {u['kind']:6s} {u['key']!r:30s} n={len(u['site_nos'])}")
