#!/usr/bin/env python3
"""
filmstrip.py — Turn a folder of images into a film strip with sprocket holes.

Usage:
    python filmstrip.py /path/to/photos
    python filmstrip.py /path/to/photos --output ~/Desktop/mystrip.png
    python filmstrip.py /path/to/photos --brand "FUJICOLOR 200" --iso "ISO 400"
    python filmstrip.py /path/to/photos --frame-width 400 --frame-height 266
    python filmstrip.py /path/to/photos --font /path/to/font.ttf
    python filmstrip.py /path/to/photos --no-text
    python filmstrip.py /path/to/photos --vertical
    python filmstrip.py /path/to/photos --grayscale

Options:
    --output, -o        Output file path (default: filmstrip.png next to input folder)
    --brand             Brand text printed on film edge (default: KODACOLOR EL)
    --iso               ISO/exposure text (default: ISO 400)
    --frame-width       Max width of each photo in px (default: 320)
    --frame-height      Max height of each photo in px (default: 213)
    --frame-gap         Gap between frames in px (default: 4)
    --no-text           Disable edge text and frame numbers
    --font              Path to a .ttf font file (falls back to system monospace fonts)
    --vertical          Arrange frames vertically instead of horizontally
    --grayscale, --bw   Convert color photos to black and white before compositing
"""

import argparse
import glob
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow is required. Run:  python3 -m pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config / constants
# ---------------------------------------------------------------------------

STRIP_COLOR = (18, 18, 18)  # near-black film base
BORDER_COLOR = (12, 12, 12)  # slightly darker border band
SPROCKET_COLOR = (38, 38, 38)  # dark grey holes (set to STRIP_COLOR for "punched" look)
TEXT_COLOR = (190, 148, 55)  # amber — classic DX edge-print color

BORDER = 44  # px — height of top/bottom dark band (or left/right if vertical)
FRAME_GAP = 4  # px — gap between photo frames (default; override with --frame-gap)
SPROCKET_W = 18  # px — sprocket hole width
SPROCKET_H = 28  # px — sprocket hole height
SPROCKET_R = 4  # px — corner radius
SPROCKET_GAP = 12  # px — spacing between holes
SPROCKET_INSET = 8  # px — distance from strip edge to hole center


# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

MONO_FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Courier.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/Library/Fonts/Courier New.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    # Windows
    "C:/Windows/Fonts/cour.ttf",
    "C:/Windows/Fonts/consola.ttf",
]


def load_font(custom_path=None, size=11):
    """Try custom path, then system monospace candidates, then PIL default."""
    candidates = ([custom_path] if custom_path else []) + MONO_FONT_CANDIDATES
    for path in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Core drawing helpers
# ---------------------------------------------------------------------------


def _text_rgba(text, font, fill):
    """Render text to a tight RGBA image."""
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bbox = probe.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((-bbox[0], -bbox[1]), text, font=font, fill=fill)
    return img


def draw_sprocket_row(draw, axis_pos, total_span, border, is_vertical, strip_dim):
    """
    Draw a row (or column) of sprocket holes.
    axis_pos: the fixed coordinate (y for horizontal, x for vertical)
    total_span: the length along the strip
    """
    pos = FRAME_GAP
    while pos < total_span - SPROCKET_W:
        if is_vertical:
            x0 = axis_pos - SPROCKET_H // 2
            y0 = pos
            x1 = axis_pos + SPROCKET_H // 2
            y1 = pos + SPROCKET_W
        else:
            x0 = pos
            y0 = axis_pos - SPROCKET_H // 2
            x1 = pos + SPROCKET_W
            y1 = axis_pos + SPROCKET_H // 2
        draw.rounded_rectangle([x0, y0, x1, y1], radius=SPROCKET_R, fill=SPROCKET_COLOR)
        pos += SPROCKET_W + SPROCKET_GAP


def draw_edge_text(
    strip,
    draw,
    brand,
    iso,
    frame_centers,
    total_w,
    total_h,
    is_vertical,
    font,
    font_small,
):
    """Print repeating brand/ISO text and per-frame numbers on the dark border strips."""
    brand_str = f"  {brand} \u25b7 {iso}  "

    if is_vertical:
        # Edge text runs along the strip length, rotated to read upright in portrait layout
        for angle, band_x_fn in ((90, lambda rw: (BORDER - rw) // 2), (270, lambda rw: total_w - BORDER + (BORDER - rw) // 2)):
            y = 4
            while y < total_h:
                label = _text_rgba(brand_str, font, TEXT_COLOR)
                rot = label.rotate(angle, expand=True, resample=Image.BICUBIC)
                x = band_x_fn(rot.width)
                strip.paste(rot, (x, y), rot)
                y += rot.height

        for i, frame_center_y in enumerate(frame_centers, start=1):
            num = _text_rgba(f"{i:02d}", font_small, TEXT_COLOR)
            rot = num.rotate(90, expand=True, resample=Image.BICUBIC)
            x = total_w - BORDER + (BORDER - rot.width) // 2
            y = frame_center_y - rot.height // 2
            strip.paste(rot, (x, y), rot)
    else:
        # Top and bottom bands
        for band_y in [4, total_h - BORDER + 5]:
            x = 0
            while x < total_w:
                draw.text((x, band_y), brand_str, fill=TEXT_COLOR, font=font)
                try:
                    x += draw.textlength(brand_str, font=font)
                except Exception:
                    x += len(brand_str) * 7

        for i, frame_center_x in enumerate(frame_centers):
            num_str = f"{i+1:02d}"
            draw.text(
                (frame_center_x - 8, total_h - BORDER + 18),
                num_str,
                fill=TEXT_COLOR,
                font=font_small,
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def make_filmstrip(
    image_folder,
    output_path=None,
    brand="KODACOLOR EL",
    iso="ISO 400",
    frame_w=320,
    frame_h=213,
    frame_gap=FRAME_GAP,
    grayscale=False,
    show_text=True,
    font_path=None,
    is_vertical=False,
):
    image_folder = Path(image_folder).expanduser().resolve()
    if not image_folder.is_dir():
        print(f"Error: '{image_folder}' is not a directory.")
        sys.exit(1)

    # Collect images
    exts = (
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp",
        "*.tiff",
        "*.bmp",
        "*.JPG",
        "*.JPEG",
        "*.PNG",
        "*.WEBP",
    )
    paths = []
    for ext in exts:
        paths.extend(image_folder.glob(ext))
    paths = sorted(paths)

    if not paths:
        print(f"No images found in '{image_folder}'.")
        sys.exit(1)

    print(f"Found {len(paths)} image(s) in {image_folder}")

    # Load and thumbnail — pack by actual size so portrait shots aren't padded in fixed slots
    frames = []
    for path in paths:
        try:
            img = Image.open(path).convert("RGB")
            if grayscale:
                img = img.convert("L").convert("RGB")
            img.thumbnail((frame_w, frame_h), Image.LANCZOS)
            frames.append((path, img))
        except Exception as e:
            print(f"  Skipping {path.name}: {e}")

    if not frames:
        print("No images could be loaded.")
        sys.exit(1)

    n = len(frames)
    gap = frame_gap
    placements = []  # (path, img, paste_x, paste_y)
    frame_centers = []

    if is_vertical:
        content_w = max(img.width for _, img in frames)
        total_w = content_w + BORDER * 2
        y = gap
        for path, img in frames:
            paste_x = BORDER + (content_w - img.width) // 2
            paste_y = y
            placements.append((path, img, paste_x, paste_y))
            frame_centers.append(paste_y + img.height // 2)
            y += img.height + gap
        total_h = y + gap
    else:
        content_h = max(img.height for _, img in frames)
        total_h = content_h + BORDER * 2
        x = gap
        for path, img in frames:
            paste_x = x
            paste_y = BORDER + (content_h - img.height) // 2
            placements.append((path, img, paste_x, paste_y))
            frame_centers.append(paste_x + img.width // 2)
            x += img.width + gap
        total_w = x + gap

    # Build strip
    strip = Image.new("RGB", (total_w, total_h), STRIP_COLOR)
    draw = ImageDraw.Draw(strip)

    # Darker border bands
    if is_vertical:
        draw.rectangle([0, 0, BORDER, total_h], fill=BORDER_COLOR)
        draw.rectangle([total_w - BORDER, 0, total_w, total_h], fill=BORDER_COLOR)
    else:
        draw.rectangle([0, 0, total_w, BORDER], fill=BORDER_COLOR)
        draw.rectangle([0, total_h - BORDER, total_w, total_h], fill=BORDER_COLOR)

    # Sprocket holes — two rows
    if is_vertical:
        draw_sprocket_row(draw, BORDER // 2, total_h, BORDER, True, total_w)
        draw_sprocket_row(draw, total_w - BORDER // 2, total_h, BORDER, True, total_w)
    else:
        draw_sprocket_row(draw, BORDER // 2, total_w, BORDER, False, total_h)
        draw_sprocket_row(draw, total_h - BORDER // 2, total_w, BORDER, False, total_h)

    # Load fonts
    font = load_font(font_path, size=11)
    font_small = load_font(font_path, size=9)

    # Edge text
    if show_text:
        draw_edge_text(
            strip,
            draw,
            brand,
            iso,
            frame_centers,
            total_w,
            total_h,
            is_vertical,
            font,
            font_small,
        )

    for i, (path, img, paste_x, paste_y) in enumerate(placements):
        strip.paste(img, (paste_x, paste_y))
        print(f"  [{i+1}/{n}] {path.name}")

    # Output path
    if output_path is None:
        output_path = image_folder.parent / "filmstrip.png"
    else:
        output_path = Path(output_path).expanduser().resolve()

    strip.save(output_path)
    print(f"\nSaved → {output_path}  ({total_w}×{total_h}px)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a film strip image from a folder of photos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("folder", help="Path to folder containing images")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (default: filmstrip.png next to input folder)",
    )
    parser.add_argument(
        "--brand",
        default="KODACOLOR EL",
        help='Brand text on film edge (default: "KODACOLOR EL")',
    )
    parser.add_argument(
        "--iso", default="ISO 400", help='ISO/speed text (default: "ISO 400")'
    )
    parser.add_argument(
        "--frame-width",
        type=int,
        default=320,
        help="Max width of each photo in px (default: 320)",
    )
    parser.add_argument(
        "--frame-height",
        type=int,
        default=213,
        help="Max height of each photo in px (default: 213)",
    )
    parser.add_argument(
        "--frame-gap",
        type=int,
        default=FRAME_GAP,
        help="Gap between frames in px (default: 4)",
    )
    parser.add_argument(
        "--no-text", action="store_true", help="Disable edge text and frame numbers"
    )
    parser.add_argument("--font", default=None, help="Path to a .ttf font file")
    parser.add_argument(
        "--vertical",
        action="store_true",
        help="Arrange frames vertically instead of horizontally",
    )
    parser.add_argument(
        "--grayscale",
        "--bw",
        action="store_true",
        help="Convert color photos to black and white before compositing",
    )

    args = parser.parse_args()

    make_filmstrip(
        image_folder=args.folder,
        output_path=args.output,
        brand=args.brand,
        iso=args.iso,
        frame_w=args.frame_width,
        frame_h=args.frame_height,
        frame_gap=args.frame_gap,
        grayscale=args.grayscale,
        show_text=not args.no_text,
        font_path=args.font,
        is_vertical=args.vertical,
    )
