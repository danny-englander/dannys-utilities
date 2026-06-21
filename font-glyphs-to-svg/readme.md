# font-glyphs-to-svg

Extract every glyph from an OpenType/TrueType font into individual SVG files, normalized to a uniform square canvas with consistent padding.

Point it at a `.otf` or `.ttf` and it writes one SVG per glyph, named by Unicode codepoint and glyph name (e.g. `U0041_A.svg`). Each glyph is measured by its real outline bounding box, scaled to fit a target content box, and centered so every icon reads at the same optical size. Glyphs with no outline (like `space`) are skipped automatically.

## Requirements

- Python 3.7+
- [fonttools](https://github.com/fonttools/fonttools)

## Getting Started

Install the one dependency:

```bash
pip install fonttools
```

Grab the script and you're ready to go:

```bash
python font-glyphs-to-svg.py YourFont.otf -o svgs
```

That's it. The output directory is created if it doesn't exist.

## Usage

```bash
python font-glyphs-to-svg.py FONT [-o OUTPUT] [--canvas CANVAS] [--padding PADDING]
```

### Arguments

| Argument | Description |
| --- | --- |
| `FONT` | Path to the `.otf` / `.ttf` font file (required) |
| `-o`, `--output` | Output directory for the SVGs (default: `svgs`) |
| `--canvas` | Square canvas size in SVG user units (default: `1000`) |
| `--padding` | Padding as a fraction of canvas per side (default: `0.08` = 8%) |

### Examples

Extract everything to the default `svgs/` folder:

```bash
python font-glyphs-to-svg.py PacificModern.otf
```

Extract to a named folder with a larger canvas and more padding:

```bash
python font-glyphs-to-svg.py PacificModern.otf -o icons --canvas 1000 --padding 0.10
```

## Output

Each glyph is written as a standalone SVG. Filenames are `U{codepoint}_{glyphname}.svg` for glyphs mapped in the font's cmap, or just `{glyphname}.svg` for unmapped glyphs (alternates, ligature components, etc.).

```
svgs/
├── U0041_A.svg
├── U0042_B.svg
├── U0061_a.svg
└── ...
```

Each file looks like this:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">
  <g transform="translate(120.000, 880.000) scale(0.760000, -0.760000) translate(-50.000, -200.000)">
    <path d="M..."/>
  </g>
</svg>
```

### Notes

- **Coordinate flip:** Fonts use a y-up coordinate system while SVG is y-down, so each path is wrapped in a flip transform rather than rewriting the path data.
- **Uniform canvas:** Every glyph is rendered on the same square `viewBox`, scaled to fit inside the content area (canvas minus padding on all sides) and centered. Icons read at a consistent optical size regardless of how they were drawn in the font.
- **Empty glyphs:** Glyphs with no outline are skipped automatically; the script reports how many were skipped when it finishes.
- **Filenames:** Glyph names are sanitized for the filesystem, so ligatures and special-character names won't break the output.

## License

MIT
