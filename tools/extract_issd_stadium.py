#!/usr/bin/env python3
"""Render an original ISSD stadium layout from a locally owned USA ROM.

The renderer uses the disassembly companion's decoded tilemap/VRAM model,
not the user-supplied temporary Field image.  It validates the exact USA ROM
before reading it and writes only a PNG plus a small provenance manifest.

Usage:
  python tools/extract_issd_stadium.py ROM.sfc OUTPUT.png
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path


EXPECTED_MD5 = "345ddedcd63412b9373dabb67c11fc05"
DEFAULT_REFERENCE_TOOLS = Path(r"C:\Users\evandro.mota\Documents\issd-native-inspect\tools")


def strip_copier_header(data: bytes) -> bytes:
    return data[512:] if len(data) % 1024 == 512 else data


def renderer(reference_tools: Path):
    if not reference_tools.is_dir():
        raise ValueError(f"reference tools directory does not exist: {reference_tools}")
    sys.path.insert(0, str(reference_tools))
    return importlib.import_module("mod_studio.stadium_geometry")


def profile(layout: int, geometry_module) -> dict:
    length, width, *_ = geometry_module.TEMPLATES[layout]
    return {
        "version": 1,
        "base_layout": layout,
        "geometry": {"length_units": length, "width_units": width},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--layout", type=int, choices=range(8), default=0,
                        help="original stadium layout ID (default: 0)")
    parser.add_argument("--reference-tools", type=Path, default=DEFAULT_REFERENCE_TOOLS,
                        help="directory containing the supplied issd-native tools package")
    args = parser.parse_args()

    rom = strip_copier_header(args.rom.read_bytes())
    digest = hashlib.md5(rom).hexdigest()
    if digest != EXPECTED_MD5:
        raise SystemExit(f"ROM MD5 {digest}; expected USA ROM {EXPECTED_MD5}")
    geometry = renderer(args.reference_tools)
    image = geometry.preview_artwork_scene(rom, profile(args.layout, geometry))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    manifest = {
        "rom_md5": digest,
        "layout": args.layout,
        "dimensions": [image.width, image.height],
        "renderer": "issd-native stadium_geometry preview_artwork_scene",
    }
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered original layout {args.layout}: {image.width}x{image.height} -> {args.output}")


if __name__ == "__main__":
    main()
