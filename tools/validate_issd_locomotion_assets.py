#!/usr/bin/env python3
"""Validate exported ROM locomotion sheets used directly by the web renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


MOTIONS = {"walking": 10, "running": 8}
KITS = ("home", "away")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path, help="dist/assets/issd/oam-teams")
    args = parser.parse_args()
    checked = 0
    for team_id in range(36):
        for kit in KITS:
            for motion, frames in MOTIONS.items():
                for direction in range(8):
                    path = args.assets / f"{team_id:02d}" / kit / f"{motion}-{direction}.png"
                    if not path.is_file():
                        raise SystemExit(f"missing locomotion sheet: {path}")
                    with Image.open(path) as image:
                        if image.mode != "RGBA":
                            raise SystemExit(f"non-RGBA locomotion sheet: {path} ({image.mode})")
                        if image.width <= 0 or image.height <= 0 or image.width % frames:
                            raise SystemExit(f"invalid {motion} frame geometry: {path} ({image.size})")
                    checked += 1
    print(f"locomotion assets: OK ({checked} ROM-derived sheets)")


if __name__ == "__main__":
    main()
