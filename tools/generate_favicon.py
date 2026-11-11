#!/usr/bin/env python3
"""Generate the Medialoft favicon.

A small "image / photo" mark (a framed tile with a sun and a mountain, the
universal picture glyph) in Medialoft's magenta/violet palette, rendered with
Pillow. Static asset served by Flask from ``app/static/`` — never through the
vulnerable ``/asset`` endpoint.

Run from the repo root:

    python tools/generate_favicon.py

Writes ``app/static/favicon.png`` (base 512 px, also downscaled to 32 px).
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

VIOLET = (124, 58, 237, 255)
VIOLET_DARK = (37, 20, 74, 255)
PAPER = (245, 243, 255, 255)
SUN = (255, 196, 84, 255)
HILL = (139, 92, 246, 255)

SIZE = 512
STATIC_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "app", "static")


def _render() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded violet background tile.
    draw.rounded_rectangle([0, 0, SIZE, SIZE], radius=int(SIZE * 0.22), fill=VIOLET)

    # Inner "photo" frame.
    m = 120
    draw.rounded_rectangle([m, m, SIZE - m, SIZE - m], radius=28, fill=PAPER)

    # Sun.
    draw.ellipse([m + 40, m + 44, m + 104, m + 108], fill=SUN)

    # Two mountains (triangles) sitting on the frame's base.
    base = SIZE - m - 20
    draw.polygon([(m + 30, base), (m + 150, base - 150), (m + 250, base)], fill=HILL)
    draw.polygon(
        [(m + 150, base), (m + 250, base - 110), (SIZE - m - 30, base)],
        fill=VIOLET_DARK,
    )

    return img


def main() -> None:
    out = os.path.abspath(STATIC_DIR)
    os.makedirs(out, exist_ok=True)
    base = _render()

    big = os.path.join(out, "favicon.png")
    base.save(big, "PNG")
    print(f"wrote {big}")

    small_path = os.path.join(out, "favicon-32.png")
    base.resize((32, 32), Image.LANCZOS).save(small_path, "PNG")
    print(f"wrote {small_path}")


if __name__ == "__main__":
    main()
