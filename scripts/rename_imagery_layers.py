# rename_imagery_layers.py — rename AFTER/BEFORE imagery layers to the date-first scheme
# and re-sort each group chronologically.
#
#   old: AFTER — caracas · pelican 0.65m · 20260627_145824_88_300d
#   new: AFTER — 06-27 · 0.65m pelican · caracas · 145824_88_300d
#
# AFTER layers use MM-DD (all 2026); BEFORE layers keep YYYY-MM-DD so 2025/2026 sort correctly.
# Alphabetical order == chronological order, so the group sort at the end just works.
#
# Run inside QGIS (Python console):  exec(open('scripts/rename_imagery_layers.py').read())
# DRY_RUN=True prints the old→new table without touching anything. Flip to False to apply.
# Idempotent: already-renamed layers are left alone.

import re
from qgis.core import QgsProject

DRY_RUN = True
GROUPS = [
    "AFTER — post-event imagery",
    "BEFORE — Vantor pre-event (stream)",
]
SENSOR_SHORT = {"worldview-2": "wv-2", "worldview-3": "wv-3", "geoeye-1": "ge-1"}
# Layers whose id carries no YYYYMMDD date (e.g. the OAM caracas-corridor COG):
# map an id substring -> "MM-DD". Leave empty to have them reported as SKIP.
DATE_OVERRIDES = {
    # "6a437f8fa8d2fe29ac06614e": "06-30",   # OAM caracas-corridor — S3 upload date; acquisition UNVERIFIED
}

OLD = re.compile(
    r"^(?P<era>AFTER|BEFORE) — (?P<loc>[^·]+?) · (?P<sensor>.+?) (?P<gsd>\d+\.\d+)m"
    r" · (?P<id>.+?)(?P<suffix> \((?:Vantor stream|Maxar)\))?$"
)
NEW_TOKEN0 = re.compile(r"^(?:\d{2}-\d{2}|\d{4}-\d{2}-\d{2})$")   # already renamed?

proj = QgsProject.instance()
root = proj.layerTreeRoot()
plan, skipped = [], []

for gname in GROUPS:
    grp = root.findGroup(gname)
    if grp is None:
        print(f"!! group not found: {gname}")
        continue
    for node in grp.findLayers():
        lyr = node.layer()
        if lyr is None:
            continue
        name = lyr.name()
        body = name.split(" — ", 1)[-1]
        if NEW_TOKEN0.match(body.split(" · ")[0]):
            continue                                    # already in new format
        m = OLD.match(name)
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
            short_id = rest if rest else "scene"
        else:
            ov = next((d for k, d in DATE_OVERRIDES.items() if k in sid), None)
            if ov is None:
                skipped.append((name, "no date in id (add to DATE_OVERRIDES)"))
                continue
            date, short_id = ov, sid
        sensor = SENSOR_SHORT.get(sensor.lower(), sensor)
        new = f"{era} — {date} · {gsd}m {sensor} · {loc} · {short_id}{suffix}"
        plan.append((lyr, name, new))

print(f"{'DRY RUN — ' if DRY_RUN else ''}{len(plan)} rename(s), {len(skipped)} skipped\n")
for _, old, new in plan:
    print(f"  {old}\n    -> {new}")
for name, why in skipped:
    print(f"  SKIP ({why}): {name}")

if not DRY_RUN:
    for lyr, _, new in plan:
        lyr.setName(new)
    # Re-sort each group's layer nodes alphabetically (= chronologically), keeping states.
    for gname in GROUPS:
        grp = root.findGroup(gname)
        if grp is None:
            continue
        entries = [(n.layer(), n.isVisible(), n.isExpanded()) for n in grp.findLayers()
                   if n.layer() is not None]
        entries.sort(key=lambda e: e[0].name())
        for n in list(grp.findLayers()):
            grp.removeChildNode(n)
        for lyr, vis, exp in entries:
            n = grp.addLayer(lyr)
            n.setItemVisibilityChecked(vis)
            n.setExpanded(exp)
    print("\nApplied. Project NOT saved — save when satisfied.")
