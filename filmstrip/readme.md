# Filmstrip

Turn a folder of photos into a single PNG that looks like a strip of 35mm film—dark borders, sprocket holes, amber edge-print text, and numbered frames.

## Requirements

- **Python 3.7+**
- **[Pillow](https://pillow.readthedocs.io/)**

No other dependencies.

## Setup

From this directory (or anywhere on your `PATH`):

```bash
python3 -m pip install Pillow
```

On macOS, `pip` is often not on your `PATH`; use `python3 -m pip` (or `pip3 install Pillow`) instead.

Optional: make the script executable and run it directly:

```bash
chmod +x filmstrip.py
./filmstrip.py /path/to/photos
```

## Quick start

Point the script at a folder of images. By default it writes `filmstrip.png` in the **parent** of that folder (not inside the photo folder).

```bash
python3 filmstrip.py /path/to/photos
```

Custom output path:

```bash
python3 filmstrip.py /path/to/photos --output ~/Desktop/mystrip.png
```

## What it does

1. Finds image files in the folder (see [Supported formats](#supported-formats)).
2. Sorts them by filename (lexicographic order).
3. Resizes each image to fit within max dimensions while preserving aspect ratio (`LANCZOS` thumbnail).
4. Packs frames edge-to-edge along the strip with only a narrow gap between them (no fixed-width padding for portrait shots).
5. Composites them onto a near-black strip with:
   - Top/bottom (or left/right in vertical mode) border bands
   - Two rows of rounded sprocket holes
   - Repeating brand + ISO text on the borders (amber, DX-style)
   - Per-frame numbers (`01`, `02`, …)
6. Saves a single RGB PNG.

Skipped files are reported on stderr; the strip still builds from the rest.

## Usage

```text
python3 filmstrip.py FOLDER [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FOLDER` | Directory containing source images (required). |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `../filmstrip.png` | Output PNG path. |
| `--brand` | | `KODACOLOR EL` | Text printed along the film edge. |
| `--iso` | | `ISO 400` | Exposure/speed text next to the brand. |
| `--frame-width` | | `320` | Max width of each photo, in pixels. |
| `--frame-height` | | `213` | Max height of each photo, in pixels. |
| `--frame-gap` | | `4` | Black gap between adjacent frames, in pixels. |
| `--no-text` | | off | Hide edge text and frame numbers. |
| `--font` | | (system mono) | Path to a `.ttf` for edge text and numbers. |
| `--vertical` | | off | Stack frames top-to-bottom instead of left-to-right. |
| `--grayscale` | `--bw` | off | Convert color photos to black and white before compositing. |

Run `python3 filmstrip.py --help` for the same list in the terminal.

## Examples

All examples use `python3` on one line. Quote any path or flag value that contains spaces.

### 1. Folder only (all defaults)

Writes `filmstrip.png` next to the parent of your photo folder. Brand `KODACOLOR EL`, ISO `ISO 400`, horizontal layout, 320×213 max frames, 4px gap.

```bash
python3 filmstrip.py ~/Pictures/cherry-blossoms
```

### 2. `--output` / `-o`

Choose where the PNG is saved (here, inside the photo folder).

```bash
python3 filmstrip.py ~/Pictures/cherry-blossoms --output ~/Pictures/cherry-blossoms/strip.png
```

Short form:

```bash
python3 filmstrip.py ./rolls/trip-2026 -o ~/Desktop/trip-filmstrip.png
```

### 3. `--brand`

Custom film stock name on the edge. Quote values that contain spaces.

```bash
python3 filmstrip.py ./photos --brand "FUJICOLOR 200"
```

### 4. `--iso`

Change only the speed / exposure text (brand stays default unless you set it too).

```bash
python3 filmstrip.py ./photos --iso "ISO 800"
```

### 5. `--brand` + `--iso`

Typical combo for a specific stock look.

```bash
python3 filmstrip.py ./photos --brand "KODAK PORTRA 400" --iso "ISO 400"
```

### 6. `--frame-width` + `--frame-height`

Larger thumbnails on the strip (still packed edge-to-edge).

```bash
python3 filmstrip.py ./photos --frame-width 480 --frame-height 320
```

### 7. `--frame-gap`

Tighter gutter between frames (default is `4`).

```bash
python3 filmstrip.py ./photos --frame-gap 2
```

Wider gutter:

```bash
python3 filmstrip.py ./photos --frame-gap 12
```

### 8. `--grayscale` / `--bw`

Convert color sources to black and white (luminance) before building the strip. Already-grayscale images are unchanged in appearance.

```bash
python3 filmstrip.py ./photos --grayscale -o ./photos-bw.png
```

Combine with vertical layout:

```bash
python3 filmstrip.py ./photos --grayscale --vertical -o ./photos-bw-vertical.png
```

### 9. `--no-text`

Strip with sprocket holes only—no brand, ISO, or frame numbers.

```bash
python3 filmstrip.py ./photos --no-text
```

### 10. `--font`

Use a specific monospace `.ttf` (macOS example).

```bash
python3 filmstrip.py ./photos --font /System/Library/Fonts/Monaco.ttf
```

### 11. `--vertical`

Stack frames top-to-bottom; edge text is rotated to read along the sides.

```bash
python3 filmstrip.py ./photos --vertical
```

### 12. `--output` + `--vertical`

Portrait-style strip saved to a named file.

```bash
python3 filmstrip.py ~/Pictures/portraits --vertical -o ~/Desktop/portraits-vertical.png
```

### 13. `--vertical` + `--no-text`

Tall strip, no edge typography.

```bash
python3 filmstrip.py ./photos --vertical --no-text -o ./vertical-clean.png
```

### 14. Frame size + gap (horizontal)

Big frames with a hairline gap between them.

```bash
python3 filmstrip.py ./photos --frame-width 400 --frame-height 266 --frame-gap 2 -o ./wide-strip.png
```

### 15. Vertical + brand + ISO + output

Full “contact sheet” style with custom stock labels.

```bash
python3 filmstrip.py "/Users/you/Projects/photos/2026/03/cherry-blossoms" --vertical --brand "KODACOLOR EL" --iso "ISO 400" -o filmstrip.png
```

### 16. Combined (most options)

Vertical roll, custom labels, larger frames, tight gap, custom font, explicit output.

```bash
python3 filmstrip.py ./archive/scans --vertical --brand "ILFORD HP5 PLUS" --iso "ISO 400" --frame-width 360 --frame-height 240 --frame-gap 3 --font "/Library/Fonts/Courier New.ttf" -o ./archive/hp5-contact-sheet.png
```

Horizontal equivalent with the same knobs (swap `--vertical` for default layout):

```bash
python3 filmstrip.py ./archive/scans --brand "ILFORD HP5 PLUS" --iso "ISO 400" --frame-width 360 --frame-height 240 --frame-gap 3 --font "/Library/Fonts/Courier New.ttf" -o ./archive/hp5-horizontal.png
```

## Supported formats

Files are matched by extension (case variants included):

`.jpg`, `.jpeg`, `.png`, `.webp`, `.tiff`, `.bmp`

Only files **directly in** `FOLDER` are used (no subfolders). Order is determined by sorted filename—rename or prefix (`01-`, `02-`, …) if you need a specific sequence.

## Output location

| `--output` | Result |
|------------|--------|
| Omitted | `{parent of FOLDER}/filmstrip.png` |
| Set | Path you provide (`~` and relative paths are expanded) |

The script prints canvas size and save path when finished, e.g. `Saved → … (2400×301px)`.

## Fonts

Edge text uses a monospace font. Resolution order:

1. `--font` if provided and readable
2. Common system paths (Courier/Monaco on macOS, DejaVu/Liberation on Linux, Courier/Consolas on Windows)
3. Pillow’s built-in default (small bitmap fallback)

For consistent results across machines, pass `--font` with a bundled `.ttf`.

## Tips

- **Aspect ratio**: Default max size is roughly 3:2 (`320×213`). Frames are packed by actual thumbnail width/height; use `--frame-gap` to tune the gutter (default `4` px).
- **Many images**: Horizontal strips grow wide; use `--vertical` or smaller `--frame-width` / `--frame-height` for very long rolls.
- **Errors**: Missing folder, empty folder, or unreadable images exit with a message; corrupt single files are skipped with a warning.

## License

Part of the [utilities](../) repo. Use and modify as you like.
