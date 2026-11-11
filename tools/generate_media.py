#!/usr/bin/env python3
"""Generate the Medialoft CDN images.

Synthetic abstract PNGs (diagonal gradient + geometric accent) rendered with
Pillow so the lab stays self-contained, lightweight and free of third-party
image licensing. Distinct from Snaptrail's photo look: these are flat,
poster-like "stock assets" a CDN would host.

Run from the repo root:

    python tools/generate_media.py

Keep ``app/config.py``'s LISTED_IMAGES in sync with these filenames.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

# (filename, label, colour A, colour B, accent)
IMAGES = [
    ("aurora.png", "Aurora", (16, 24, 48), (28, 92, 120), (120, 255, 190)),
    ("cityscape.png", "Cityscape", (30, 20, 48), (90, 40, 110), (255, 170, 90)),
    ("desert.png", "Desert", (196, 140, 74), (240, 205, 140), (120, 70, 40)),
    ("forest.png", "Forest", (16, 48, 32), (40, 110, 70), (210, 240, 180)),
    ("ocean.png", "Ocean", (10, 40, 70), (20, 110, 150), (190, 240, 255)),
    ("peaks.png", "Peaks", (60, 70, 92), (150, 165, 190), (255, 255, 255)),
]

SIZE = 600
OUT_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "media")


def _diagonal_gradient(a: tuple[int, int, int], b: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE))
    px = img.load()
    for y in range(SIZE):
        for x in range(0, SIZE, 4):
            t = (x + y) / (2 * SIZE)
            col = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
            for dx in range(4):
                if x + dx < SIZE:
                    px[x + dx, y] = col
    return img


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _render(spec: tuple) -> Image.Image:
    filename, label, a, b, accent = spec
    img = _diagonal_gradient(a, b)
    draw = ImageDraw.Draw(img, "RGBA")

    # A geometric accent: concentric rings in one corner.
    cx, cy = int(SIZE * 0.78), int(SIZE * 0.24)
    for r in range(140, 20, -28):
        alpha = 70 if (r // 28) % 2 else 130
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r], outline=accent + (alpha,), width=6
        )

    # A thin baseline for a poster feel.
    draw.rectangle([0, int(SIZE * 0.84), SIZE, int(SIZE * 0.845)], fill=accent + (200,))

    # Label.
    font = _load_font(44)
    draw.text((42, SIZE - 96), label, font=font, fill=(255, 255, 255, 240))
    small = _load_font(20)
    draw.text((44, SIZE - 46), "medialoft · cdn", font=small, fill=accent + (235,))

    return img


def main() -> None:
    out = os.path.abspath(OUT_DIR)
    os.makedirs(out, exist_ok=True)
    for spec in IMAGES:
        img = _render(spec)
        path = os.path.join(out, spec[0])
        img.save(path, "PNG")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
