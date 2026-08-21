"""Export the geer_mapping inventory to a KMZ with the GEER metadata statement.

    uv run python reports/export_mapping_kmz.py

The KML Document <description> (what Google Earth shows when the top-level
layer is clicked) is read from the layer's metadata Abstract — the text the
GEER team approved. It is looked up in order:

  1. inside data/landslide_candidates/geer_mapping.gpkg (Layer Properties ->
     Metadata -> paste into Abstract -> Metadata menu -> "Save as Default"),
  2. the layer metadata stored in qgis/geer_venezuela.qgz.

The script fails loudly if neither holds an abstract, so the KMZ can never
ship without the statement. Placemarks carry the eight inventory attributes;
features are foldered and colored by Type.
"""

from __future__ import annotations

import re
import sqlite3
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import geopandas as gpd
import simplekml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
GPKG = REPO / "data" / "landslide_candidates" / "geer_mapping.gpkg"
QGZ = REPO / "qgis" / "geer_venezuela.qgz"
OUT = HERE / "geer_venezuela_mapping_inventory.kmz"

FIELDS = ["Confidence", "Type", "Comments", "Source", "Access", "Impact",
          "Latitude", "Longitude"]

TYPE_COLORS = {  # KML aabbggrr via simplekml.Color.rgb
    "Landslide": simplekml.Color.rgb(230, 60, 30),
    "Liquefaction": simplekml.Color.rgb(30, 120, 230),
    "Ground Rupture": simplekml.Color.rgb(160, 40, 200),
    "Ground Settlement": simplekml.Color.rgb(230, 170, 0),
}
DEFAULT_COLOR = simplekml.Color.rgb(120, 120, 120)


def abstract_from_gpkg() -> str | None:
    with sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True) as con:
        try:
            rows = con.execute(
                "SELECT m.metadata FROM gpkg_metadata m "
                "JOIN gpkg_metadata_reference r ON r.md_file_id = m.id "
                "WHERE r.table_name = 'geer_mapping'"
            ).fetchall()
        except sqlite3.OperationalError:  # no metadata tables yet
            return None
    for (xml,) in rows:
        try:
            el = ElementTree.fromstring(xml).find(".//abstract")
        except ElementTree.ParseError:
            continue
        if el is not None and el.text and el.text.strip():
            return el.text.strip()
    return None


def abstract_from_project() -> str | None:
    with zipfile.ZipFile(QGZ) as z:
        qgs = next(n for n in z.namelist() if n.endswith(".qgs"))
        root = ElementTree.fromstring(z.read(qgs))
    for ml in root.iter("maplayer"):
        ds = ml.findtext("datasource") or ""
        if "geer_mapping.gpkg" in ds:
            el = ml.find(".//resourceMetadata/abstract")
            if el is not None and el.text and el.text.strip():
                return el.text.strip()
    return None


def placemark_description(row) -> str:
    tr = "".join(
        f"<tr><td><b>{f}</b></td><td>{row[f] if row[f] not in (None, '') else '—'}</td></tr>"
        for f in FIELDS
    )
    return f"<table border='0' cellpadding='2'>{tr}</table>"


def main() -> None:
    abstract = abstract_from_gpkg() or abstract_from_project()
    if not abstract:
        raise SystemExit(
            "No metadata abstract found for geer_mapping.\n"
            "Layer Properties -> Metadata -> Identification -> Abstract, paste the\n"
            "GEER statement, then Metadata menu -> 'Save as Default' (or save the\n"
            "project) and re-run."
        )

    gdf = gpd.read_file(GPKG, layer="geer_mapping", fid_as_index=True).to_crs(4326)

    kml = simplekml.Kml(name="GEER Venezuela — ground deformation inventory (2026-06-24 EQs)")
    kml.document.description = abstract

    styles: dict[str, simplekml.Style] = {}
    for t, color in {**TYPE_COLORS, "Unclassified": DEFAULT_COLOR}.items():
        st = simplekml.Style()
        st.linestyle.color = color
        st.linestyle.width = 3
        styles[t] = st

    folders: dict[str, simplekml.Folder] = {}
    n = 0
    for _, row in gdf.iterrows():
        t = row.get("Type") or "Unclassified"
        if t not in folders:
            folders[t] = kml.newfolder(name=t)
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        parts = geom.geoms if geom.geom_type.startswith("Multi") else [geom]
        name = f"{t} {row.name}"  # row.name = gpkg fid
        for part in parts:
            ls = folders[t].newlinestring(name=name, coords=list(part.coords),
                                          description=placemark_description(row))
            ls.style = styles.get(t, styles["Unclassified"])
        n += 1

    kml.savekmz(str(OUT))
    print(f"wrote {OUT.name}: {n} features in {len(folders)} Type folders")
    print(f"document description: {len(abstract)} chars, starts: {abstract[:60]!r}")


if __name__ == "__main__":
    main()
