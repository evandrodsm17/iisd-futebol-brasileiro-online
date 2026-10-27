"""Decode the eight-direction walking/running descriptor scripts from ISSD ROM."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


SCRIPTS = {"walking": 0xCEF8, "running": 0xCF9F}


def offset(address: int) -> int:
    """Map a bank-$82 LoROM pointer to its headerless file offset."""
    return 0x10000 + (address & 0x7FFF)


def word(rom: bytes, address: int) -> int:
    return struct.unpack_from("<H", rom, offset(address))[0]


def decode(rom: bytes, script: int) -> list[dict[str, object]]:
    directions = []
    for direction in range(8):
        pointer = word(rom, script + direction * 2)
        descriptors = []
        for index in range(64):
            raw = word(rom, pointer + index * 2)
            descriptors.append(raw | 0x8000)
            if raw < 0x8000:
                break
        else:
            raise ValueError(f"unterminated script ${pointer:04X}")
        directions.append({"direction": direction, "pointer": f"$82:{pointer:04X}", "descriptors": descriptors})
    return directions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    if len(rom) != 0x200000:
        raise ValueError("expected a 2 MiB headerless USA ROM")
    payload = {
        "source": {"rom_md5": hashlib.md5(rom).hexdigest(), "bank": "$82"},
        "cycles": {
            name: {"script": f"$82:{address:04X}", "directions": decode(rom, address)}
            for name, address in SCRIPTS.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
