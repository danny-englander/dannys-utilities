# font_to_svg

Extract every glyph from an OpenType/TrueType font into individual SVG files.

Point it at a `.otf` or `.ttf` and it writes one SVG per glyph, named by Unicode codepoint and glyph name (e.g. `U0041_A.svg`). Handles the font-to-SVG coordinate flip, sizes the `viewBox` to the glyph, and can skip non-drawing glyphs like `space`.

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
python font_to_svg.py YourFont.otf -o svgs
```

That's it. The output directory is created if it doesn't exist.

## Usage

```bash
python font_to_svg.py FONT [-o OUTPUT] [--skip-empty]
```

### Arguments

| Argument | Description |
| --- | --- |
| `FONT` | Path to the `.otf` / `.ttf` font file (required) |
| `-o`, `--output` | Output directory for the SVGs (default: `svgs`) |
| `--skip-empty` | Skip glyphs with no outline, like `space` |

### Examples

Extract everything to the default `svgs/` folder:

```bash
python font_to_svg.py PacificModern.otf
```

Extract to a named folder, skipping blank glyphs:

```bash
python font_to_svg.py PacificModern.otf -o icons --skip-empty
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
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 1000">
  <g transform="translate(0, 1000) scale(1, -1)">
    <path d="M..."/>
  </g>
</svg>
```

### Notes

- **Coordinate flip:** Fonts use a y-up coordinate system while SVG is y-down, so each path is wrapped in a flip transform rather than rewriting the path data.
- **viewBox:** Sized to the glyph's advance width and the font's units-per-em, so glyphs keep their natural proportions and spacing.
- **Filenames:** Glyph names are sanitized for the filesystem, so ligatures and special-character names won't break the output.

## License

MIT
