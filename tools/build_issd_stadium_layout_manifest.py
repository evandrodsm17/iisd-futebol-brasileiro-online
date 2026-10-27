"""Build a browser stadium manifest from extracted ISS Deluxe preview PNGs.

Each preview has a black outer canvas.  The crop is its exact non-black RGB
bounds, matching the existing layout-0 crop instead of using guessed values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


NAMES = ("Japan", "USA", "Spain", "Italy", "England", "Germany", "Brazil", "Nigeria")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stadium_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    layouts = []
    for layout, name in enumerate(NAMES):
        image_path = args.stadium_directory / f"layout-{layout}.png"
        image = Image.open(image_path).convert("RGB")
        bounds = ImageChops.difference(image, Image.new("RGB", image.size)).getbbox()
        if bounds is None:
            raise ValueError(f"empty stadium preview: {image_path}")
        left, top, right, bottom = bounds
        layouts.append({
            "id": layout,
            "name": name,
            "asset": f"./assets/issd/stadium/layout-{layout}.png",
            "image": {"width": image.width, "height": image.height},
            "crop": {"x": left, "y": top, "w": right - left, "h": bottom - top},
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"source": "ROM-derived stadium preview bounds", "layouts": layouts}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
