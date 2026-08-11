#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the application icon (an envelope) with Pillow.

The icon is original artwork drawn from primitives, so the repository carries
no third-party or company-owned image.

Usage::

    python assets/make_icon.py

Produces ``assets/app_icon.png`` (256x256) and ``assets/app_icon.ico``
(multi-resolution, used by the Windows build).
"""

import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 256

BACKGROUND = (37, 99, 165, 255)   # deep blue
ENVELOPE = (255, 255, 255, 255)   # white body
FLAP = (222, 232, 245, 255)       # light blue-grey flap
OUTLINE = (23, 63, 110, 255)      # dark blue outline


def rounded_background(draw: ImageDraw.ImageDraw) -> None:
    """Draw the rounded square background."""
    draw.rounded_rectangle([(0, 0), (SIZE - 1, SIZE - 1)], radius=48, fill=BACKGROUND)


def envelope(draw: ImageDraw.ImageDraw) -> None:
    """Draw a simple envelope centred in the icon."""
    left, top = 40, 72
    right, bottom = SIZE - 40, SIZE - 72
    draw.rounded_rectangle([(left, top), (right, bottom)], radius=12, fill=ENVELOPE,
                           outline=OUTLINE, width=4)

    middle_x = (left + right) / 2
    fold_y = top + (bottom - top) * 0.62

    # Flap: two triangles meeting at the centre fold.
    draw.polygon([(left, top), (right, top), (middle_x, fold_y)], fill=FLAP, outline=OUTLINE)
    draw.line([(left, top), (middle_x, fold_y), (right, top)], fill=OUTLINE, width=4, joint="curve")

    # Lower creases, for depth.
    draw.line([(left, bottom), (middle_x - 20, fold_y - 6)], fill=OUTLINE, width=3)
    draw.line([(right, bottom), (middle_x + 20, fold_y - 6)], fill=OUTLINE, width=3)


def build() -> None:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    rounded_background(draw)
    envelope(draw)

    png_path = os.path.join(HERE, "app_icon.png")
    ico_path = os.path.join(HERE, "app_icon.ico")
    image.save(png_path, "PNG")
    image.save(
        ico_path,
        "ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Written: {png_path}")
    print(f"Written: {ico_path}")


if __name__ == "__main__":
    build()
