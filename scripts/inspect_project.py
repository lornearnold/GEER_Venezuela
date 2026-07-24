"""Show what the Layers panel cannot: the actual layer registry.

Run inside QGIS: Plugins > Python Console > Show Editor > open this > Run.
Read-only - changes nothing.

The Layers panel is a *view* onto the project, not the project itself. A layer can
be loaded and renderable with no row in the panel; two panel rows can share a name;
a row can point at a file that no longer exists. This script prints the registry as
it really is, and flags the four conditions that make name-based scripts pick the
wrong layer:

    DUPLICATE NAME   two+ layers share a name -> a name lookup is a coin flip
    SAME SOURCE      one file loaded twice    -> edits may hit the copy you can't see
    NOT IN PANEL     loaded but no tree node  -> renders on the map, unclickable
    INVALID          source missing/unreadable -> queries silently return nothing

A clean report means name-based lookups in the other scripts are safe right now.

    python inspect_project.py            # summary + problems
    (edit VERBOSE below for the full layer listing)
"""

from __future__ import annotations

import collections
from pathlib import Path

from qgis.core import QgsLayerTreeGroup, QgsProject

VERBOSE = False  # True -> list every layer, not just the problems


def _tree_layer_ids(node, found=None) -> set:
    """Layer ids that actually have a row in the Layers panel."""
    if found is None:
        found = set()
    for child in node.children():
        layer = child.layer() if hasattr(child, "layer") else None
        if layer is not None:
            found.add(layer.id())
        if isinstance(child, QgsLayerTreeGroup):
            _tree_layer_ids(child, found)
    return found


def inspect() -> int:
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    registry = project.mapLayers()
    in_panel = _tree_layer_ids(root)

    groups = []

    def walk_groups(node, path=""):
        for child in node.children():
            if isinstance(child, QgsLayerTreeGroup):
                groups.append(f"{path}/{child.name()}")
                walk_groups(child, f"{path}/{child.name()}")

    walk_groups(root)

    print("=" * 68)
    print(f"registry (real layers):     {len(registry)}")
    print(f"rows in the Layers panel:   {len(in_panel)}")
    print(f"groups (panel-only, no data): {len(groups)}")
    print("=" * 68)

    problems = 0

    # 1. Duplicate names - the main hazard for name-based lookups.
    by_name = collections.defaultdict(list)
    for layer in registry.values():
        by_name[layer.name()].append(layer)
    dupes = {n: ls for n, ls in by_name.items() if len(ls) > 1}
    if dupes:
        problems += len(dupes)
        print(f"\nDUPLICATE NAME ({len(dupes)}) - name lookups here are ambiguous:")
        for name, layers in dupes.items():
            print(f"  '{name}' x{len(layers)}")
            for layer in layers:
                print(f"      {layer.id()}")
                print(f"      {layer.source()[:88]}")

    # 2. One file loaded more than once.
    by_source = collections.defaultdict(list)
    for layer in registry.values():
        by_source[layer.source().split("|")[0]].append(layer.name())
    multi = {s: n for s, n in by_source.items() if len(n) > 1}
    if multi:
        problems += len(multi)
        print(f"\nSAME SOURCE ({len(multi)}) - one file, several layers:")
        for source, names in multi.items():
            print(f"  {Path(source).name or source[:60]}")
            for name in names:
                print(f"      loaded as: {name}")

    # 3. Loaded but invisible in the panel.
    hidden = [registry[i] for i in set(registry) - in_panel]
    if hidden:
        problems += len(hidden)
        print(f"\nNOT IN PANEL ({len(hidden)}) - loaded, renderable, no row to click:")
        for layer in hidden:
            print(f"  {layer.name()}   [{layer.id()[:44]}]")

    # 4. Broken sources.
    invalid = [l for l in registry.values() if not l.isValid()]
    if invalid:
        problems += len(invalid)
        print(f"\nINVALID ({len(invalid)}) - source missing or unreadable:")
        for layer in invalid:
            print(f"  {layer.name()}")
            print(f"      {layer.source()[:88]}")

    if not problems:
        print("\nNo ambiguity found. Name-based lookups are safe in this project.")
    else:
        print(f"\n{problems} condition(s) that can make a script touch the wrong layer.")

    if VERBOSE:
        print("\n" + "-" * 68)
        print("every layer in the registry:")
        for layer in sorted(registry.values(), key=lambda l: l.name()):
            panel = " " if layer.id() in in_panel else "!"  # ! = not in panel
            kind = "raster" if layer.__class__.__name__ == "QgsRasterLayer" else "vector"
            print(f" {panel} [{kind}] {layer.name()}")
            print(f"        {layer.source()[:84]}")

    return 1 if problems else 0


# No __main__ guard: the QGIS Python console's Run button executes a file WITHOUT
# setting __name__ to "__main__", so a guarded call would silently do nothing.
# Running this module is the whole point, so just call it.
inspect()
