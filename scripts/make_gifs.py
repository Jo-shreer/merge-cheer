#!/usr/bin/env python3
"""Turn the owned stills into small looping GIFs for PR comments.

Motion is a short brightness pulse plus a tiny zoom. Extra per-frame
particles explode the file size and look noisy at comment width.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
STILLS = ROOT / "stills"
GIFS = ROOT / "gifs"
SIZE = 280
FRAMES = 6
COLORS = 48
DURATION_MS = 110
MAX_BYTES = 180 * 1024
NAMES = (
    "celebration",
    "ship-it",
    "nailed-it",
    "nice-work",
    "high-five",
    "cleanup",
)


def _square(src: Path) -> Image.Image:
    image = Image.open(src).convert("RGB")
    image.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (SIZE, SIZE), (18, 20, 26))
    canvas.paste(image, ((SIZE - image.width) // 2, (SIZE - image.height) // 2))
    return canvas


def _frame(base: Image.Image, index: int) -> Image.Image:
    wave = math.sin(2 * math.pi * index / FRAMES)
    zoomed = 1.0 + 0.018 * (0.5 + 0.5 * wave)
    crop = max(2, int(SIZE * (1 - 1 / zoomed) / 2))
    frame = base.crop((crop, crop, SIZE - crop, SIZE - crop)).resize(
        (SIZE, SIZE), Image.Resampling.LANCZOS
    )
    frame = ImageEnhance.Brightness(frame).enhance(1.0 + 0.04 * wave)
    return frame.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT)


def render(src: Path, dest: Path) -> None:
    base = _square(src)
    frames = [_frame(base, index) for index in range(FRAMES)]
    dest.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        dest,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> int:
    missing = [name for name in NAMES if not (STILLS / f"{name}.png").is_file()]
    if missing:
        print(f"missing stills: {', '.join(missing)}", file=sys.stderr)
        return 1
    for name in NAMES:
        dest = GIFS / f"{name}.gif"
        render(STILLS / f"{name}.png", dest)
        size = dest.stat().st_size
        print(f"{dest.name} {size // 1024} KB")
        if size > MAX_BYTES:
            print(f"{dest.name} is over {MAX_BYTES // 1024} KB", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
