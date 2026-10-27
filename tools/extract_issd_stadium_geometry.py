"""Extract the eight ISS Deluxe USA stadium geometry records from a ROM file.

The table begins at CPU address $81:EC47.  For a headerless LoROM image that
maps to file offset $00:EC47.  The output contains only decoded numeric
metadata, never graphics or ROM bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


CPU_ADDRESS = "$81:EC47"
FILE_OFFSET = 0xEC47
LAYOUT_COUNT = 8


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    if len(rom) != 0x200000:
        raise ValueError(f"expected 2 MiB headerless USA ROM, got {len(rom)} bytes")
    records = []
    for layout in range(LAYOUT_COUNT):
        length, width = struct.unpack_from("<HH", rom, FILE_OFFSET + layout * 4)
        records.append({"layout": layout, "length": length, "width": width})
    payload = {
        "source": {
            "rom_md5": hashlib.md5(rom).hexdigest(),
            "table_cpu_address": CPU_ADDRESS,
            "table_file_offset": f"0x{FILE_OFFSET:05X}",
            "format": "eight little-endian length/width pairs",
        },
        "layouts": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
