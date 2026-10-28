"""Resolve static ISSD action descriptors to ROM graphics sources and assets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from resolve_issd_animation_assets import asset_ranges, read_descriptor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("actions", type=Path, help="issd-action-scripts.json")
    parser.add_argument("asset_pointers", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    source = json.loads(args.actions.read_text(encoding="utf-8"))
    ranges = asset_ranges(args.asset_pointers)
    resolved: dict[str, dict] = {}
    for action in source["actions"].values():
        for direction in action["directions"]:
            for descriptor in direction["descriptors"]:
                key = f"${descriptor:04X}"
                if key in resolved:
                    continue
                data = read_descriptor(rom, descriptor)
                graphics_source = data["graphics_source"]
                asset = next(
                    (name for start, end, name in ranges if start <= graphics_source <= end),
                    None,
                )
                resolved[key] = {
                    "pose": f"${data['pose']:04X}",
                    "graphics_source": f"${graphics_source:06X}",
                    "detail": data["detail"],
                    "trailing_geometry": data["trailing_geometry"],
                    "trailing_selector": data["trailing_selector"],
                    "asset": asset,
                }
    payload = {
        "source": source["source"],
        "evidence": "static-rom-descriptor-resolution",
        "limitations": source["limitations"],
        "actions": source["actions"],
        "descriptors": resolved,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
