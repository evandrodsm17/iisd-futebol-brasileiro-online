"""Index the ISS Deluxe compressed OAM records from a locally supplied ROM.

The program writes metadata only (addresses, byte ranges and headers).  It
does not copy ROM data into the repository.  The resulting index is the input
for the browser's future SNES OAM compositor.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ENTRY = re.compile(r"^\s*dl \$(?P<start>[0-9A-F]{6}),\$(?P<end>[0-9A-F]{6}),(?P<name>[^,\s]+)", re.MULTILINE)


def lorom_offset(address: int) -> int:
    if address & 0x8000 == 0:
        raise ValueError(f"{address:06X} is not a LoROM data address")
    return ((address >> 16) & 0x7F) * 0x8000 + (address & 0x7FFF)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("asset_pointers", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    entries = []
    for match in ENTRY.finditer(args.asset_pointers.read_text(encoding="utf-8")):
        start, end = int(match["start"], 16), int(match["end"], 16)
        if not (0x988000 <= start < 0x98C077):
            continue
        offset, end_offset = lorom_offset(start), lorom_offset(end)
        payload = rom[offset:end_offset]
        entries.append({
            "name": match["name"],
            "snes_range": f"${start:06X}-${end:06X}",
            "rom_offset": f"0x{offset:06X}",
            "byte_length": len(payload),
            "header_byte_0": payload[0] if payload else None,
            # Kept as a raw header interpretation until runtime correlation
            # proves the individual record boundaries.
            "header_bytes_1_2_be": int.from_bytes(payload[1:3], "big") if len(payload) >= 3 else None,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"format": "issd-snes-compressed-oam-v1", "entries": entries}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
