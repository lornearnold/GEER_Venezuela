# rename_imagery_layers.py — rename AFTER/BEFORE imagery layers to the date-first scheme
# and re-sort each group chronologically.
#
#   target: 06-27 · 0.65m pelican · caracas · 145824_88_300d
#
# No era prefix — the group (and zone) names already say AFTER/BEFORE. AFTER layers use
# MM-DD (all 2026); BEFORE layers keep YYYY-MM-DD so 2025/2026 sort correctly. Alphabetical
# order == chronological order. Handles all three name generations (original location-first,
# the interim "AFTER — date · …" form, and the final form — final names are left alone).
#
# Run inside QGIS (Python console):  exec(open('scripts/rename_imagery_layers.py').read())
# DRY_RUN=True prints the old→new table without touching anything. Flip to False to apply.

import re
from qgis.core import QgsProject

DRY_RUN = False
GROUPS = [
    "AFTER — post-event imagery",
    "BEFORE — Vantor pre-event (stream)",
]
SENSOR_SHORT = {"worldview-2": "wv-2", "worldview-3": "wv-3", "geoeye-1": "ge-1"}
# Layers whose id carries no YYYYMMDD date (e.g. the OAM caracas-corridor COG):
# map an id substring -> "MM-DD". Leave empty to have them reported as SKIP.
DATE_OVERRIDES = {
    # OAM caracas-corridor = Vantor open-data collect B0300011000DFB10 (WV-2, 2026-06-27 15:15 UTC),
    # confirmed via OAM API bbox search 2026-07-27.
    "6a437f8fa8d2fe29ac06614e": "06-27",
}

DATE_RX = r"\d{2}-\d{2}|\d{4}-\d{2}-\d{2}"
P_OLD = re.compile(   # original: AFTER — <loc> · <sensor> <gsd>m · <id>
    r"^(?P<era>AFTER|BEFORE) — (?P<loc>[^·]+?) · (?P<sensor>.+?) (?P<gsd>\d+\.\d+)m"
    r" · (?P<id>.+?)(?P<suffix> \((?:Vantor stream|Maxar)\))?$")
P_MID = re.compile(   # interim: AFTER — <date> · <gsd>m <sensor> · <loc> · <id>
    rf"^(?P<era>AFTER|BEFORE) — (?P<date>{DATE_RX}) · (?P<gsd>\d+\.\d+)m (?P<sensor>[^·]+?)"
    r" · (?P<loc>[^·]+?) · (?P<id>.+?)(?P<suffix> \((?:Vantor stream|Maxar)\))?$")
P_FINAL = re.compile(rf"^(?:{DATE_RX}) · ")

proj = QgsProject.instance()
root = proj.layerTreeRoot()
plan, skipped = [], []

for gname in GROUPS:
    grp = root.findGroup(gname)
    if grp is None:
        print(f"!! group not found: {gname}")
        continue
    era_default = gname.split(" — ")[0]
    for node in grp.findLayers():
        lyr = node.layer()
        if lyr is None:
            continue
        name = lyr.name()
        if P_FINAL.match(name):
            continue                                    # already in final form
        m = P_MID.match(name)
        if m:
            date, gsd, sensor, loc, sid = (m["date"], m["gsd"], m["sensor"].strip(),
                                           m["loc"].strip(), m["id"].strip())
            suffix = m["suffix"] or ""
        else:
            m = P_OLD.match(name)
            if not m:
                skipped.append((name, "unrecognized pattern"))
                continue
            era, loc, sensor, gsd, sid = (m["era"], m["loc"].strip(), m["sensor"].strip(),
                                          m["gsd"], m["id"].strip())
            suffix = m["suffix"] or ""
            dm = re.match(r"^(\d{4})(\d{2})(\d{2})[_ ]?(.*)$", sid)
            if dm:
                yyyy, mm, dd, rest = dm.groups()
                date = f"{mm}-{dd}" if era == "AFTER" else f"{yyyy}-{mm}-{dd}"
                sid = rest if rest else "scene"
            else:
                ov = next((d for k, d in DATE_OVERRIDES.items() if k in sid), None)
                if ov is None:
                    skipped.append((name, "no date in id (add to DATE_OVERRIDES)"))
                    continue
                date = ov
            sensor = SENSOR_SHORT.get(sensor.lower(), sensor)
        new = f"{date} · {gsd}m {sensor} · {loc} · {sid}{suffix}"
        plan.append((lyr, name, new))

print(f"{'DRY RUN — ' if DRY_RUN else ''}{len(plan)} rename(s), {len(skipped)} skipped\n")
for _, old, new in plan:
    print(f"  {old}\n    -> {new}")
for name, why in skipped:
    print(f"  SKIP ({why}): {name}")

if not DRY_RUN:
    for lyr, _, new in plan:
        lyr.setName(new)
    # Re-sort each group's layer nodes alphabetically (= chronologically).
    # Clone-then-remove one node at a time: every layer keeps >=1 tree reference at all
    # times, clone() preserves checked/expanded state, and the registry is verified after.
    n_before = len(proj.mapLayers())
    for gname in GROUPS:
        grp = root.findGroup(gname)
        if grp is None:
            continue
        for node in sorted(grp.findLayers(),
                           key=lambda n: n.layer().name() if n.layer() else ""):
            clone = node.clone()
            grp.addChildNode(clone)       # append in sorted order...
            grp.removeChildNode(node)     # ...then drop the original
    assert len(proj.mapLayers()) == n_before, \
        "layer registry changed during re-sort — investigate before saving!"
    print("\nApplied. Project NOT saved — save when satisfied.")
