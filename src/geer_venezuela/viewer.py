"""Map interaction helpers."""

from __future__ import annotations


def add_compare_control(m, layers: dict[str, str], selected: str | None = None, position: str = "topleft"):
    """Pin a persistent one-click view switcher (e.g. BEFORE / AFTER / TOPO) to a leafmap Map.

    `layers` maps button labels to layer names already added to the map; exactly one is
    visible at a time. `selected` is the initial view (default: last label). Returns the
    ToggleButtons widget.
    """
    import ipywidgets as widgets
    from ipyleaflet import WidgetControl

    resolved = {}
    for label, name in layers.items():
        matches = [layer for layer in m.layers if getattr(layer, "name", "") == name]
        if not matches:
            raise ValueError(f"No layer named {name!r} on the map (for button {label!r})")
        resolved[label] = matches[-1]

    selected = selected or list(resolved)[-1]
    for label, layer in resolved.items():
        layer.visible = label == selected

    buttons = widgets.ToggleButtons(
        options=list(resolved),
        value=selected,
        style=widgets.ToggleButtonsStyle(button_width="70px"),
    )

    def _switch(change):
        for label, layer in resolved.items():
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
