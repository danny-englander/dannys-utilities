#!/usr/bin/env python3
"""
Extract every glyph from an OpenType/TrueType font into individual SVG files,
normalizing each glyph to a uniform square canvas with consistent padding.

Each icon is measured by its real outline bounding box, scaled to fit a target
content box, and centered. The result: every icon reads at the same optical
size regardless of how it was drawn in the font.

Usage:
    python font_to_svg.py path/to/font.otf -o output_dir
    python font_to_svg.py font.otf -o svgs --canvas 1000 --padding 0.10
"""

import argparse
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen


def glyph_to_svg(glyph_set, glyph_name, canvas, padding):
    """Render one glyph into a square `canvas`x`canvas` viewBox.

    The glyph's outline bounding box is scaled uniformly to fit inside a
    content box of side `canvas * (1 - 2*padding)`, then centered. Returns
    None for glyphs with no outline (space, etc.).
    """
    glyph = glyph_set[glyph_name]

    # Measure the real ink bounds (not the advance width).
    bounds_pen = BoundsPen(glyph_set)
    glyph.draw(bounds_pen)
    if bounds_pen.bounds is None:
        return None  # empty outline -> skip

    x_min, y_min, x_max, y_max = bounds_pen.bounds
    glyph_w = x_max - x_min
    glyph_h = y_max - y_min
    if glyph_w <= 0 or glyph_h <= 0:
        return None

    # Target content box (canvas minus padding on all sides).
    content = canvas * (1.0 - 2.0 * padding)
    scale = content / max(glyph_w, glyph_h)

    # Capture the raw path in font units.
    path_pen = SVGPathPen(glyph_set)
    glyph.draw(path_pen)
    path_data = path_pen.getCommands()

    # Centering offsets, in *scaled* units, within the canvas.
    scaled_w = glyph_w * scale
    scaled_h = glyph_h * scale
    tx = (canvas - scaled_w) / 2.0
    ty = (canvas - scaled_h) / 2.0

    # Transform pipeline (applied right-to-left in SVG):
    #   1. translate glyph so its bbox origin sits at (0,0): -x_min, -y_min
    #   2. scale uniformly
    #   3. flip Y (font is y-up, SVG y-down)
    #   4. translate into centered position on the canvas
    #
    # Combined: translate(tx, canvas - ty) scale(scale, -scale) translate(-x_min, -y_min)
    transform = (
        f"translate({tx:.3f}, {canvas - ty:.3f}) "
        f"scale({scale:.6f}, {-scale:.6f}) "
        f"translate({-x_min:.3f}, {-y_min:.3f})"
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {canvas} {canvas}">\n'
        f'  <g transform="{transform}">\n'
        f'    <path d="{path_data}"/>\n'
        f"  </g>\n"
        f"</svg>\n"
    )
    return svg


def sanitize(name):
    return "".join(c if c.isalnum() or c in "-_." else f"_{ord(c)}_" for c in name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font", help="Path to .otf/.ttf font file")
    ap.add_argument("-o", "--output", default="svgs", help="Output directory")
    ap.add_argument(
        "--canvas",
        type=int,
        default=1000,
        help="Square canvas size in SVG user units (default: 1000)",
    )
    ap.add_argument(
        "--padding",
        type=float,
        default=0.08,
        help="Padding as a fraction of canvas per side (default: 0.08 = 8%%)",
    )
    args = ap.parse_args()

    font = TTFont(args.font)
    glyph_set = font.getGlyphSet()

    os.makedirs(args.output, exist_ok=True)

    cmap = font.getBestCmap()
    name_to_unicode = {v: k for k, v in cmap.items()}

    count = 0
    skipped = 0
    for glyph_name in font.getGlyphOrder():
        svg = glyph_to_svg(glyph_set, glyph_name, args.canvas, args.padding)
        if svg is None:
            skipped += 1
            continue

        uni = name_to_unicode.get(glyph_name)
        prefix = f"U{uni:04X}_" if uni is not None else ""
        fname = f"{prefix}{sanitize(glyph_name)}.svg"

        with open(os.path.join(args.output, fname), "w") as f:
            f.write(svg)
        count += 1

    print(
        f"Wrote {count} SVG files to {args.output}/ "
        f"(skipped {skipped} empty glyphs)"
    )


if __name__ == "__main__":
    main()
