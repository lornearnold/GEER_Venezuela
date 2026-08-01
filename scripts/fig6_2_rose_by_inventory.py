#!/usr/bin/env python
"""Fig. 6.2 variants — landslide aspect rose split by inventory, slope-agnostic.

The pooled rose (scripts/fig6_2_aspect_rose.py) mixes two inventories that
occupy non-overlapping ground: the GeoSyntec polygons sit on the Ávila massif,
the GEER-mapped lines run west along the coastal range. A pooled aspect
distribution therefore cannot show whether the NE trend is present in *both*
datasets or is inherited from one region's terrain. These variants separate
them. Slope is dropped entirely — the question here is inventory agreement,
not steepness.

Two renderings, because the obvious one has a geometry trap:

  --mode split (default)
      Each 22.5 deg sector is divided down the middle: GeoSyntec occupies the
      counter-clockwise half, GEER the clockwise half, each drawn to its own
      radius. Angle now carries two meanings (compass direction AND which
      inventory), which is the compromise the user asked to see. Because the
      two halves span equal angles, the half with the larger radius is the one
      with more features — but the *areas* are no longer comparable to a normal
      rose, since each half-petal covers half the angular width. Read radius,
      not area.

  --mode facet
      Two side-by-side roses, one per inventory, on a shared radial scale.
      Area keeps its usual meaning within each panel and the trend can be
      compared directly. Nothing is overloaded.

Deliberately NOT offered: stacking the two inventories in one petal. Stacked
radius would make the outer segment's area depend on how many features the
inner one has, so equal counts would render as unequal wedges. That misstates
the data rather than merely compressing it.

Counts are normalized to percent-within-inventory by default (--counts for raw)
because the inventories differ in size (456 vs 226); raw counts would show the
larger inventory dominating every direction regardless of trend.

Run from the repo root:

    uv run python scripts/fig6_2_rose_by_inventory.py
    uv run python scripts/fig6_2_rose_by_inventory.py --mode facet
    uv run python scripts/fig6_2_rose_by_inventory.py --counts --scale 0.8

Reads only; safe to run while QGIS has the project open.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fig6_2_aspect_rose import (  # noqa: E402  (sibling script, same dir)
    GEER_LINES,
    GEOSYNTEC,
    REPO,
    feature_aspects,
    load_grids,
    sectorize,
)

import geopandas as gpd  # noqa: E402

OUT_DIR = REPO / "06_Landslides"

# One color per inventory. Distinct hues (not a ramp) — these are nominal
# categories, not ordered classes.
INV_COLORS = {"GeoSyntec (Area A)": "#1f78b4",
              "GEER-mapped (Area B)": "#e08214"}

plt.rcParams["font.family"] = ["Arial", "Helvetica", "sans-serif"]

LABELS16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
CARDINALS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def style_axes(ax, n, theta, rlabel=True):
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    if n == 16:
        ax.set_xticks(theta)
        ax.set_xticklabels([lab if lab in CARDINALS else "" for lab in LABELS16],
                           fontsize=11)
    ax.tick_params(axis="y", labelsize=9, colors="0.4")
    ax.yaxis.grid(True, color="0.85", linewidth=0.8)
    ax.xaxis.grid(True, color="0.85", linewidth=0.8)
    ax.spines["polar"].set_color("0.7")
    ax.set_rlabel_position(200)
    if not rlabel:
        ax.set_yticklabels([])


def circular_mean_of_sectors(counts, n):
    """Resultant direction and length of a sector histogram (for the console)."""
    ang = np.arange(n) * (2 * np.pi / n)
    w = counts / counts.sum() if counts.sum() else counts
    s, c = (w * np.sin(ang)).sum(), (w * np.cos(ang)).sum()
    return np.degrees(np.arctan2(s, c)) % 360.0, float(np.hypot(s, c))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode",
                    choices=("split", "facet", "widthcount", "stacked", "overlay"),
                    default="split")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--sectors", type=int, default=16)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--counts", action="store_true",
                    help="plot raw counts instead of percent-within-inventory")
    args = ap.parse_args()

    grids = load_grids()
    print("DEMs:", ", ".join(name for name, *_ in grids))

    gs = gpd.read_file(GEOSYNTEC)
    gs = gs[gs.Type == "Landslide"]
    poly_asp, _ = feature_aspects(gs, grids, "polygon")

    lines = gpd.read_file(GEER_LINES, layer="geer_mapping")
    line_asp, _ = feature_aspects(lines, grids, "line")

    n = args.sectors
    series = {}
    for label, asp in (("GeoSyntec (Area A)", poly_asp),
                       ("GEER-mapped (Area B)", line_asp)):
        a = asp[~np.isnan(asp)]
        counts = np.bincount(sectorize(a, n), minlength=n).astype(float)
        series[label] = counts
        mu, R = circular_mean_of_sectors(counts, n)
        print(f"{label}: n={int(counts.sum())}, resultant {mu:.0f}deg, "
              f"concentration R={R:.2f}")

    # Percent-within-inventory unless raw counts were asked for: the inventories
    # differ ~2x in size, so raw counts compare sample size, not orientation.
    plot = {}
    for label, counts in series.items():
        plot[label] = counts if args.counts else 100.0 * counts / counts.sum()
    unit = "features" if args.counts else "% of inventory"

    if n == 16:
        print(f"\n{'sector':>6} " + " ".join(f"{lab:>12}" for lab in series))
        for j in range(n):
            row = " ".join(f"{plot[lab][j]:>12.1f}" for lab in series)
            print(f"{LABELS16[j]:>6} {row}")

    theta = np.arange(n) * (2 * np.pi / n)
    sector = 2 * np.pi / n
    side = 6.5 * args.scale
    pad = 0.32

    if args.mode == "split":
        # Each sector split in half: one inventory per half, own radius.
        legend_strip = 2.60
        fig_w, fig_h = side + legend_strip, side + 2 * pad
        fig = plt.figure(figsize=(fig_w, fig_h))
        ax = fig.add_axes([pad / fig_w, pad / fig_h, side / fig_w, side / fig_h],
                          projection="polar")
        half = sector * 0.5 * 0.92  # 0.92 leaves a hairline gap between sectors
        for i, (label, vals) in enumerate(plot.items()):
            # i=0 -> counter-clockwise half, i=1 -> clockwise half
            offset = (-0.25 if i == 0 else 0.25) * sector
            ax.bar(theta + offset, vals, width=half, bottom=0.0,
                   color=INV_COLORS[label], edgecolor="white", linewidth=0.8,
                   label=label, align="center")
        style_axes(ax, n, theta)
        ax.legend(title=f"Inventory ({unit})", loc="upper left",
                  bbox_to_anchor=(1.0, 0.95), frameon=False,
                  fontsize=10, title_fontsize=10)
        note = ("Each sector is split in half\n"
                "by inventory. Compare the\n"
                "halves by RADIUS, not area:\n"
                "each half spans half a sector,\n"
                "so areas are not comparable\n"
                "to a conventional rose.")
        fig.text((side + 0.12) / fig_w, 0.05, note, fontsize=8.5,
                 color="0.35", va="bottom", ha="left", linespacing=1.5)
        default = OUT_DIR / "fig6_2_rose_split_by_inventory.png"
    elif args.mode == "stacked":
        # Requested for comparison. NOTE the distortion: stacking counts along a
        # radius means the outer segment is drawn at a larger radius, so equal
        # counts render as unequal areas -- the outer inventory always looks
        # bigger than it is. Included to see, not recommended to publish.
        legend_strip = 2.60
        fig_w, fig_h = side + legend_strip, side + 2 * pad
        fig = plt.figure(figsize=(fig_w, fig_h))
        ax = fig.add_axes([pad / fig_w, pad / fig_h, side / fig_w, side / fig_h],
                          projection="polar")
        bottom = np.zeros(n)
        for label, vals in plot.items():
            ax.bar(theta, vals, width=sector * 0.95, bottom=bottom,
                   color=INV_COLORS[label], edgecolor="white", linewidth=1.0,
                   label=label)
            bottom += vals
        style_axes(ax, n, theta)
        ax.legend(title=f"Inventory ({unit})", loc="upper left",
                  bbox_to_anchor=(1.0, 0.95), frameon=False,
                  fontsize=10, title_fontsize=10)
        note = ("CAUTION: stacking on a radius\n"
                "distorts area. The outer (orange)\n"
                "segment sits at a larger radius,\n"
                "so equal counts draw as unequal\n"
                "wedges and the outer inventory\n"
                "looks larger than it is.")
        fig.text((side + 0.12) / fig_w, 0.05, note, fontsize=8.5,
                 color="0.35", va="bottom", ha="left", linespacing=1.5)
        default = OUT_DIR / "fig6_2_rose_stacked_by_inventory.png"
    elif args.mode == "overlay":
        # Both petals share the sector and start at the origin; the smaller
        # inventory is drawn narrower and on top, so both are readable at once
        # and every petal is visible even where one is much shorter.
        legend_strip = 2.60
        fig_w, fig_h = side + legend_strip, side + 2 * pad
        fig = plt.figure(figsize=(fig_w, fig_h))
        ax = fig.add_axes([pad / fig_w, pad / fig_h, side / fig_w, side / fig_h],
                          projection="polar")
        order = sorted(plot, key=lambda k: series[k].sum(), reverse=True)
        for depth, label in enumerate(order):
            back = depth == 0
            # Front petals are 3/4 the width of the back ones and carry no
            # outline, so they read as a layer on top rather than as their own
            # wedges competing with the back petals' edges.
            wide = sector * (0.95 if back else 0.95 * 0.75)
            ax.bar(theta, plot[label], width=wide, bottom=0.0,
                   color=INV_COLORS[label],
                   edgecolor=("white" if back else "none"),
                   linewidth=(1.0 if back else 0.0),
                   zorder=2 + depth, label=label)
        style_axes(ax, n, theta)
        ax.legend(title=f"Inventory ({unit})", loc="upper left",
                  bbox_to_anchor=(1.0, 0.95), frameon=False,
                  fontsize=10, title_fontsize=10)
        note = ("Both petals start at the origin\n"
                "and share the sector; the smaller\n"
                "inventory is drawn narrower and\n"
                "in front. Where orange overhangs\n"
                "blue, Area B has more features in\n"
                "that direction than Area A.")
        fig.text((side + 0.12) / fig_w, 0.05, note, fontsize=8.5,
                 color="0.35", va="bottom", ha="left", linespacing=1.5)
        default = OUT_DIR / "fig6_2_rose_overlay_by_inventory.png"
    elif args.mode == "widthcount":
        # Length = % within inventory (comparable across the 2x size gap),
        # width = count (so sample size is visible as petal fatness).
        # Width cannot BE the count -- a 75-count petal would wrap the circle --
        # so counts map onto a fraction of the half-sector each inventory owns,
        # with a floor so a 1-count petal stays visible. Area is then roughly
        # "% x count", a sample-weighted quantity with no direct reading; the
        # two channels are meant to be read separately.
        legend_strip = 2.60
        fig_w, fig_h = side + legend_strip, side + 2 * pad
        fig = plt.figure(figsize=(fig_w, fig_h))
        ax = fig.add_axes([pad / fig_w, pad / fig_h, side / fig_w, side / fig_h],
                          projection="polar")
        half = sector * 0.5
        cmax = max(c.max() for c in series.values())
        wmin, wmax = 0.18, 0.92  # fraction of the half-sector
        for i, (label, vals) in enumerate(plot.items()):
            counts = series[label]
            widths = half * (wmin + (wmax - wmin) * (counts / cmax))
            offset = (-0.25 if i == 0 else 0.25) * sector
            ax.bar(theta + offset, vals, width=widths, bottom=0.0,
                   color=INV_COLORS[label], edgecolor="white", linewidth=0.8,
                   label=label, align="center")
        style_axes(ax, n, theta)
        ax.legend(title=f"Inventory\nlength = {unit}", loc="upper left",
                  bbox_to_anchor=(1.0, 0.95), frameon=False,
                  fontsize=10, title_fontsize=10)
        # Width legend: a few reference counts drawn as plain swatches.
        ticks = [t for t in (5, 25, 50, int(cmax)) if t <= cmax]
        lines_ = [f"width = feature count", ""]
        for t in ticks:
            lines_.append(f"  {'█' * max(1, round(1 + 5 * t / cmax))}  {t}")
        fig.text((side + 0.12) / fig_w, 0.30, "\n".join(lines_), fontsize=8.5,
                 color="0.35", va="bottom", ha="left", linespacing=1.6,
                 family="monospace")
        note = ("Length is comparable between\n"
                "inventories; width shows how\n"
                "many features back each petal.\n"
                "Area mixes both — read the two\n"
                "channels separately.")
        fig.text((side + 0.12) / fig_w, 0.05, note, fontsize=8.5,
                 color="0.35", va="bottom", ha="left", linespacing=1.5)
        default = OUT_DIR / "fig6_2_rose_widthcount_by_inventory.png"
    else:
        # Two panels, shared radial limit, area keeps its usual meaning.
        gap = 1.00  # room for the inner panel's E label and the outer's W
        title_h = 0.55
        fig_w = 2 * side + gap + 2 * pad
        fig_h = side + 2 * pad + title_h
        fig = plt.figure(figsize=(fig_w, fig_h))
        rmax = max(v.max() for v in plot.values()) * 1.05
        width = sector * 0.95
        for i, (label, vals) in enumerate(plot.items()):
            left = (pad + i * (side + gap)) / fig_w
            ax = fig.add_axes([left, pad / fig_h, side / fig_w, side / fig_h],
                              projection="polar")
            ax.bar(theta, vals, width=width, bottom=0.0,
                   color=INV_COLORS[label], edgecolor="white", linewidth=1.0)
            style_axes(ax, n, theta, rlabel=(i == 0))
            ax.set_ylim(0, rmax)
            fig.text(left + (side / fig_w) / 2,
                     (pad + side + 0.10) / fig_h,
                     f"{label}   n={int(series[label].sum())}   ({unit})",
                     fontsize=11, ha="center", va="bottom")
        default = OUT_DIR / "fig6_2_rose_facet_by_inventory.png"

    out = args.out or default
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
