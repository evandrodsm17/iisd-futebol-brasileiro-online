"""Decode a 544-byte SNES OAM mirror captured with capture_issd_oam.lua."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = [line.strip() for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = bytes.fromhex("".join(lines))
    planes = [bytes.fromhex(line) for line in lines] if len(lines) == 4 and all(len(bytes.fromhex(line)) == 256 for line in lines) else None
    if planes:
        slots = []
        for index in range(256):
            x, y, tile, properties = (plane[index] for plane in planes)
            if x == y == tile == properties == 0:
                continue
            slots.append({"slot": index, "x": x, "y": y, "tile": tile, "palette": (properties >> 1) & 7,
                          "priority": (properties >> 4) & 3, "h_flip": bool(properties & 0x40), "v_flip": bool(properties & 0x80)})
        args.output.write_text(json.dumps({"format": "issd-planar-oam-v1", "slots": slots}, indent=2), encoding="utf-8")
        return
    if len(data) != 544:
        raise ValueError(f"expected 544 OAM bytes, found {len(data)}")

    slots = []
    for index in range(128):
        x, y, tile, properties = data[index * 4:index * 4 + 4]
        high = (data[512 + index // 4] >> ((index % 4) * 2)) & 0b11
        # $F0/$F0 is ISSD's cleared OAM slot. Keep only real objects.
        if x == y == tile == properties == 0xF0:
            continue
        slots.append({
            "slot": index,
            "x": x | ((high & 1) << 8),
            "y": y,
            "tile": tile,
            "palette": (properties >> 1) & 0b111,
            "priority": (properties >> 4) & 0b11,
            "h_flip": bool(properties & 0x40),
            "v_flip": bool(properties & 0x80),
            "large_object": bool(high & 0b10),
        })

    args.output.write_text(json.dumps({"format": "snes-oam-slots-v1", "slots": slots}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
