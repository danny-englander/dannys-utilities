#!/usr/bin/env python3
"""
Extract every glyph from an OpenType/TrueType font into individual SVG files.

Usage:
    python font_to_svg.py path/to/font.otf -o output_dir
"""

import argparse
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen


def glyph_to_svg(font, glyph_set, glyph_name, units_per_em):
    glyph = glyph_set[glyph_name]
    pen = SVGPathPen(glyph_set)
    glyph.draw(pen)
    path_data = pen.getCommands()

    width = glyph.width or units_per_em

    # Flip Y: font coords are y-up, SVG is y-down. Use a transform group.
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {units_per_em}">\n'
        f'  <g transform="translate(0, {units_per_em}) scale(1, -1)">\n'
        f'    <path d="{path_data}"/>\n'
        f"  </g>\n"
        f"</svg>\n"
    )
    return svg


def sanitize(name):
    # Make glyph names safe for filenames
    return "".join(c if c.isalnum() or c in "-_." else f"_{ord(c)}_" for c in name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font", help="Path to .otf/.ttf font file")
    ap.add_argument("-o", "--output", default="svgs", help="Output directory")
    ap.add_argument(
        "--skip-empty",
        action="store_true",
        help="Skip glyphs with no outline (e.g. space)",
    )
    args = ap.parse_args()

    font = TTFont(args.font)
    glyph_set = font.getGlyphSet()
    units_per_em = font["head"].unitsPerEm

    os.makedirs(args.output, exist_ok=True)

    # Build reverse cmap so we can also name files by unicode where available
    cmap = font.getBestCmap()
    name_to_unicode = {v: k for k, v in cmap.items()}

    count = 0
    for glyph_name in font.getGlyphOrder():
        glyph = glyph_set[glyph_name]
        svg = glyph_to_svg(font, glyph_set, glyph_name, units_per_em)

        # Detect empty outline
        if args.skip_empty and 'd=""' in svg:
            continue

        uni = name_to_unicode.get(glyph_name)
        prefix = f"U{uni:04X}_" if uni is not None else ""
        fname = f"{prefix}{sanitize(glyph_name)}.svg"

        with open(os.path.join(args.output, fname), "w") as f:
            f.write(svg)
        count += 1

    print(f"Wrote {count} SVG files to {args.output}/")


if __name__ == "__main__":
    main()
