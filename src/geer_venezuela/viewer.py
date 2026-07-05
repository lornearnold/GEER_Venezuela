"""Map interaction helpers."""

from __future__ import annotations

import json

#: Default tag categories for landslide reconnaissance marking
TAG_CATEGORIES = (
    "Confidence: high",
    "Confidence: med",
    "Confidence: low",
    "Priority: high",
    "Priority: med.",
    "Priority: low",
)


def add_compare_control(
    m,
    layers: dict[str, str | list[str]],
    selected: str | None = None,
    position: str = "topleft",
):
    """Pin a persistent one-click view switcher (e.g. BEFORE / AFTER / TOPO) to a leafmap Map.

    `layers` maps button labels to a layer name (or list of names, shown together) already
    added to the map; exactly one label's layers are visible at a time. `selected` is the
    initial view (default: last label). Returns the ToggleButtons widget.
    """
    import ipywidgets as widgets
    from ipyleaflet import WidgetControl

    resolved: dict[str, list] = {}
    for label, names in layers.items():
        if isinstance(names, str):
            names = [names]
        group = []
        for name in names:
            matches = [
                layer for layer in m.layers if getattr(layer, "name", "") == name
            ]
            if not matches:
                raise ValueError(
                    f"No layer named {name!r} on the map (for button {label!r})"
                )
            group.append(matches[-1])
        resolved[label] = group

    selected = selected or list(resolved)[-1]
    for label, group in resolved.items():
        for layer in group:
            layer.visible = label == selected

    buttons = widgets.ToggleButtons(
        options=list(resolved),
        value=selected,
        style=widgets.ToggleButtonsStyle(button_width="70px"),
    )

    def _switch(change):
        for label, group in resolved.items():
            for layer in group:
                layer.visible = label == change["new"]

    buttons.observe(_switch, "value")
    m.add(WidgetControl(widget=buttons, position=position))
    return buttons


def add_flicker_control(m, layer_name: str | None = None, position: str = "topleft"):
    """Pin a persistent one-click BEFORE/AFTER toggle button to a leafmap Map.

    Toggles visibility of the layer named `layer_name` (default: the topmost layer
    whose name starts with "AFTER"). Returns the button so a keyboard shortcut or
    other widget can drive it too.
    """
    import ipywidgets as widgets
    from ipyleaflet import WidgetControl

    candidates = [
        layer
        for layer in m.layers
        if (layer_name and getattr(layer, "name", "") == layer_name)
        or (layer_name is None and getattr(layer, "name", "").startswith("AFTER"))
    ]
    if not candidates:
        raise ValueError(f"No layer found to flicker (layer_name={layer_name!r})")
    layer = candidates[-1]

    button = widgets.ToggleButton(
        value=True,
        description="Showing: AFTER",
        tooltip="Click to flicker between BEFORE and AFTER",
        layout=widgets.Layout(width="150px"),
    )

    def _toggle(change):
        layer.visible = change["new"]
        button.description = "Showing: AFTER" if change["new"] else "Showing: BEFORE"

    button.observe(_toggle, "value")
    m.add(WidgetControl(widget=button, position=position))
    return button


def add_tagging_control(
    m, categories: tuple[str, ...] = TAG_CATEGORIES, position: str = "topright"
):
    """Pin a tag panel to the map: every feature drawn afterwards gets the panel's
    current category + note stamped into its properties.

    Tagged features accumulate on `m.tagged_features` (deleting a feature with the
    draw tools removes it from the list too). Save with `save_tagged_features(m, path)`.
    """
    import ipywidgets as widgets
    from ipyleaflet import WidgetControl

    m.tagged_features = []

    category = widgets.Dropdown(
        options=categories, description="tag:", layout=widgets.Layout(width="230px")
    )
    note = widgets.Text(
        placeholder="optional note…",
        description="note:",
        layout=widgets.Layout(width="230px"),
    )
    counter = widgets.HTML("0 tagged")
    panel = widgets.VBox([category, note, counter])

    def _key(geo_json):
        return json.dumps(geo_json.get("geometry"), sort_keys=True)

    def _on_draw(control, action, geo_json, **kwargs):
        if action == "created":
            feature = dict(geo_json)
            feature["properties"] = {
                **(geo_json.get("properties") or {}),
                "category": category.value,
                "note": note.value,
            }
            m.tagged_features.append(feature)
        elif action == "deleted":
            key = _key(geo_json)
            m.tagged_features = [f for f in m.tagged_features if _key(f) != key]
        counter.value = f"{len(m.tagged_features)} tagged"

    m.draw_control.on_draw(_on_draw)
    m.add(WidgetControl(widget=panel, position=position))
    return panel


def add_site_editor(
    m,
    sites,
    categories: tuple[str, ...] = TAG_CATEGORIES,
    layer_name: str = "Marked candidates",
    position: str = "topright",
):
    """Add saved sites to the map as a clickable, editable layer.

    Click a feature to select it (turns red), then use the pinned editor panel to
    re-tag it (category + note) or delete it. Edits live on `m.sites_gdf`; persist
    them with `save_sites(m.sites_gdf, ...)`.
    """
    import ipywidgets as widgets
    from ipyleaflet import GeoJSON, WidgetControl

    gdf = sites.reset_index(drop=True).copy()
    for column in ("category", "note"):
        if column not in gdf.columns:
            gdf[column] = None
    m.sites_gdf = gdf

    state = {"selected": None}

    def _data():
        return json.loads(m.sites_gdf.to_json())

    def _style(feature):
        selected = state["selected"] is not None and str(feature.get("id")) == str(
            state["selected"]
        )
        return {
            "color": "#ff3b30" if selected else "#ffd60a",
            "weight": 4 if selected else 3,
            "fillOpacity": 0.5 if selected else 0.3,
        }

    layer = GeoJSON(
        data=_data(),
        style_callback=_style,
        point_style={"radius": 7},
        hover_style={"weight": 5},
        name=layer_name,
    )
    m.add(layer)

    header = widgets.HTML("<b>Site editor</b> — click a feature")
    category = widgets.Dropdown(
        options=categories, description="tag:", layout=widgets.Layout(width="230px")
    )
    note = widgets.Text(
        placeholder="optional note…",
        description="note:",
        layout=widgets.Layout(width="230px"),
    )
    apply_btn = widgets.Button(
        description="Apply tag",
        button_style="primary",
        layout=widgets.Layout(width="110px"),
    )
    delete_btn = widgets.Button(
        description="Delete site",
        button_style="danger",
        layout=widgets.Layout(width="110px"),
    )
    status = widgets.HTML("")
    panel = widgets.VBox(
        [header, category, note, widgets.HBox([apply_btn, delete_btn]), status]
    )

    def _refresh():
        layer.data = _data()

    def _on_click(**kwargs):
        feature = kwargs.get("feature") or {}
        site_id = feature.get("id")
        if site_id is None:
            return
        state["selected"] = int(site_id)
        row = m.sites_gdf.loc[state["selected"]]
        header.value = f"<b>Site {site_id}</b> — {row.get('source', '')}"
        if row.get("category") in categories:
            category.value = row["category"]
        note.value = row.get("note") or ""
        status.value = ""
        _refresh()

    def _apply(_):
        if state["selected"] is None:
            status.value = "Select a feature first."
            return
        m.sites_gdf.loc[state["selected"], ["category", "note"]] = [
            category.value,
            note.value,
        ]
        status.value = f"Site {state['selected']} tagged: {category.value}"
        _refresh()

    def _delete(_):
        if state["selected"] is None:
            status.value = "Select a feature first."
            return
        deleted = state["selected"]
        m.sites_gdf = m.sites_gdf.drop(index=deleted).reset_index(drop=True)
        state["selected"] = None
        header.value = "<b>Site editor</b> — click a feature"
        status.value = f"Site {deleted} deleted ({len(m.sites_gdf)} remain)"
        _refresh()

    layer.on_click(_on_click)
    apply_btn.on_click(_apply)
    delete_btn.on_click(_delete)
    m.add(WidgetControl(widget=panel, position=position))
    return panel


def save_sites(gdf, geojson_dir=None, kmz_file=None) -> list:
    """Persist (edited) sites: per-source GeoJSON files and/or a combined KMZ.

    GeoJSON files are grouped by the `source` column and overwrite the originals.
    The KMZ follows GEER's KML-product convention: one placemark per site, named by
    site number only; tags/notes/source travel as ExtendedData metadata (visible in
    Google Earth's placemark balloon). Returns the list of files written.
    """
    from pathlib import Path

    import simplekml

    written = []
    if geojson_dir is not None:
        for source, group in gdf.groupby("source"):
            path = Path(geojson_dir) / f"{source}.geojson"
            group.drop(columns=["source"]).to_file(path)
            written.append(path)
    if kmz_file is not None:
        kml = simplekml.Kml(name="Landslide candidates")
        for i, row in gdf.iterrows():
            name = f"{i:03d}"
            metadata = {
                key: row[key]
                for key in ("source", "category", "note")
                if key in row.index and row[key]
            }
            geometry = row.geometry
            parts = (
                list(geometry.geoms)
                if geometry.geom_type.startswith("Multi")
                else [geometry]
            )
            for part in parts:
                if part.geom_type == "Point":
                    placemark = kml.newpoint(name=name, coords=[(part.x, part.y)])
                elif part.geom_type == "Polygon":
                    placemark = kml.newpolygon(
                        name=name, outerboundaryis=list(part.exterior.coords)
                    )
                    placemark.style.polystyle.color = simplekml.Color.changealphaint(
                        90, simplekml.Color.yellow
                    )
                    placemark.style.linestyle.color = simplekml.Color.yellow
                    placemark.style.linestyle.width = 2
                elif part.geom_type == "LineString":
                    placemark = kml.newlinestring(name=name, coords=list(part.coords))
                    placemark.style.linestyle.color = simplekml.Color.yellow
                    placemark.style.linestyle.width = 3
                else:
                    continue
                for key, value in metadata.items():
                    placemark.extendeddata.newdata(name=key, value=str(value))
        kml.savekmz(str(kmz_file))
        written.append(Path(kmz_file))
    return written


def save_tagged_features(m, out_file) -> int:
    """Write features tagged via `add_tagging_control` to GeoJSON; returns the count.

    Falls back to the plain drawn features (no tags) if the tagging control wasn't used.
    """
    import geopandas as gpd

    features = getattr(m, "tagged_features", None)
    if not features:
        features = (m.user_rois or {}).get("features", [])
    if not features:
        return 0
    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    gdf.to_file(out_file)
    return len(gdf)
