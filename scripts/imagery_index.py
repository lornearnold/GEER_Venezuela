"""Shared rules for what counts as a dated imagery scene.

All three navigation scripts import from here so they agree on one definition.
Runs inside the QGIS Python console (needs qgis.core).

Two things are defined here, and they are the knobs worth editing:

    SERVICE_MARKERS  layer-name substrings that mark a *continuous or composite*
                     product (NASA services, Wayback, hillshade). These are
                     excluded: they have no single capture instant, so putting
                     them on a time slider would misrepresent them.

    scene_date()     pulls a capture date out of a layer name. Handles both
                     naming schemes in this project:
                         'PS 2026-06-29 150034 - 2510'          -> 2026-06-29
                         'AFTER - la-guaira - pelican 0.62m - 20260626_150535' -> 2026-06-26
"""

from __future__ import annotations

import re
from datetime import date

# Substrings marking a streaming/composite layer with no single capture date.
# Anything matching is skipped by every script here.
SERVICE_MARKERS = (
    "NASA",
    "Wayback",
    "Black Marble",
    "OPERA",
    "NISAR",
    "Landsat",
    "Sentinel",
    "Satellogic",
    "DISASTERS_",
    "Esri World Hillshade",
    "OpenStreetMap",
    "Slope (degrees)",
)

# 2026-06-29 / 2026_06_29 / 20260629, also 1999-12-27 for the historical aerials.
_DATE_RE = re.compile(r"((?:19|20)\d{2})[-_]?(\d{2})[-_]?(\d{2})")


def is_service_layer(name: str) -> bool:
    """True for streaming/composite layers that should stay off the time slider."""
    return any(marker in name for marker in SERVICE_MARKERS)


# Date-first scheme (since 2026-07-27): AFTER layers are 'MM-DD · <gsd>m <sensor> · <loc> · <id>'
# with the year implied (all post-event imagery is 2026); BEFORE layers keep YYYY-MM-DD.
_DATE_FIRST_RE = re.compile(r"^(\d{2})-(\d{2}) · ")
IMPLIED_YEAR = 2026
_SENSOR_LONG = {"wv-2": "worldview-2", "wv-3": "worldview-3", "ge-1": "geoeye-1"}


def _date_first_tokens(name: str) -> list[str] | None:
    """['MM-DD'|'YYYY-MM-DD', '<gsd>m <sensor>', '<loc>', '<id>'] for date-first names, else None."""
    parts = [p.strip() for p in name.split(" · ")]
    if len(parts) >= 3 and re.match(r"^(\d{2}-\d{2}|\d{4}-\d{2}-\d{2})$", parts[0]):
        return parts
    return None


def scene_date(name: str) -> date | None:
    """Capture date parsed from a layer name, or None if it has none.

    Rejects impossible month/day values so a stray scene id like '..._9999_13'
    cannot masquerade as a date.
    """
    m = _DATE_FIRST_RE.match(name)
    if m:
        try:
            return date(IMPLIED_YEAR, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    for match in _DATE_RE.finditer(name):
        year, month, day = (int(g) for g in match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            continue  # not a real calendar date; keep looking
    return None


def sensor_of(name: str) -> str:
    """Best-effort sensor label from the layer name ('' when unknown)."""
    toks = _date_first_tokens(name)
    if toks:
        m = re.match(r"^[\d.\-–]+\s*m\s+(.+)$", toks[1])  # '0.34m wv-3' -> 'wv-3'
        if m:
            short = m.group(1).strip().lower()
            return _SENSOR_LONG.get(short, short)
    for sensor in ("skysat", "pelican", "worldview-2", "worldview-3", "vantor",
                   "aerial mosaic"):
        if sensor in name.lower():
            return sensor
    if name.startswith("PS "):
        return "planetscope"
    return ""


def location_of(name: str) -> str:
    """AOI name from the 'AFTER - <location> - ...' convention ('' when absent)."""
    toks = _date_first_tokens(name)
    if toks:
        return toks[2]
    parts = [p.strip() for p in name.split("·")]
    if len(parts) >= 2 and (name.startswith("AFTER") or name.startswith("BEFORE")):
        head = parts[0]
        for prefix in ("AFTER — ", "BEFORE-1999 — ", "BEFORE — "):
            if head.startswith(prefix):
                return head[len(prefix):].strip()
    return ""


def gsd_of(name: str) -> float | None:
    """Ground sample distance in metres, parsed from e.g. 'pelican 0.62m'."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*m\b", name)
    return float(match.group(1)) if match else None


def dated_rasters(project) -> list[tuple[object, date]]:
    """Every raster layer in the project that is a dated scene, with its date.

    Sorted oldest first. Service layers and undated rasters are skipped.
    """
    out = []
    for layer in project.mapLayers().values():
        if layer.__class__.__name__ != "QgsRasterLayer":
            continue
        name = layer.name()
        if is_service_layer(name):
            continue
        captured = scene_date(name)
        if captured is None:
            continue
        out.append((layer, captured))
    return sorted(out, key=lambda pair: pair[1])
