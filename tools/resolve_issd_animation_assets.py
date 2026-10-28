"""Resolve live ISSD descriptors to named graphic ranges in the disassembly."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


LABEL = re.compile(r"^(GFX_[A-Za-z0-9_]+)_Ptrs:\s*$")
RANGE = re.compile(r"\bdl \$(?P<start>[0-9A-F]{6}),\$(?P<end>[0-9A-F]{6})")


def lorom_offset(address: int) -> int:
    if address & 0xFFFF < 0x8000:
        raise ValueError(f"not a LoROM address: ${address:06X}")
    return ((address >> 16) & 0x7F) * 0x8000 + (address & 0x7FFF)


def read_descriptor(rom: bytes, descriptor: int) -> dict:
    offset = lorom_offset(0x820000 | descriptor)
    data = rom[offset:offset + 9]
    if len(data) != 9:
        raise ValueError(f"descriptor exceeds ROM: ${descriptor:04X}")
    return {
        "pose": data[0] | data[1] << 8,
        "graphics_source": data[2] | data[3] << 8 | data[4] << 16,
        "detail": data[5],
        "trailing_geometry": f"${data[6] | data[7] << 8:04X}",
        "trailing_selector": data[8],
    }


def asset_ranges(path: Path) -> list[tuple[int, int, str]]:
    ranges, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        label = LABEL.match(line)
        if label:
            current = label.group(1)
            continue
        item = RANGE.search(line)
        if item and current:
            ranges.append((int(item.group("start"), 16), int(item.group("end"), 16), current))
    return ranges


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace_report", type=Path)
    parser.add_argument("asset_pointers", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    report = json.loads(args.trace_report.read_text(encoding="utf-8"))
    ranges = asset_ranges(args.asset_pointers)
    scripts = []
    for script in report["scripts"]:
        frames = []
        for text, count in script["descriptors"].items():
            descriptor = int(text[1:], 16)
            try:
                resolved = read_descriptor(rom, descriptor)
            except ValueError as error:
                frames.append({"descriptor": text, "samples": count, "error": str(error)})
                continue
            source = resolved["graphics_source"]
            # The pointer entries name DMA end addresses and several observed
            # descriptors point exactly at that boundary for their second row.
            asset = next((name for start, end, name in ranges if start <= source <= end), None)
            frames.append({
                "descriptor": text,
                "samples": count,
                "pose": f"${resolved['pose']:04X}",
                "graphics_source": f"${source:06X}",
                "detail": resolved["detail"],
                "trailing_geometry": resolved["trailing_geometry"],
                "trailing_selector": resolved["trailing_selector"],
                "asset": asset,
            })
        scripts.append({**script, "frames": frames})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "evidence": report["evidence"],
        "trace_valid_samples": report["valid_samples"],
        "asset_pointer_source": str(args.asset_pointers),
        "scripts": scripts,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
