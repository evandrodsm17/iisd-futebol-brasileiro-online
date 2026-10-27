"""Compose one ISSD player pose from ROM graphics and observed OAM parts.

This is intentionally strict.  Running descriptors in the USA ROM reference
dynamic pose geometry in WRAM, therefore this tool refuses to invent X/Y
positions.  Its composition JSON must have come from a same-frame emulator
capture and must name the 16-bit descriptor that supplied the two graphics
rows.  The ROM is read locally and is never copied to the output directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


TILE_BYTES = 32


def lorom_offset(address: int) -> int:
    if address & 0xFFFF < 0x8000:
        raise ValueError(f"not a LoROM address: ${address:06X}")
    return ((address >> 16) & 0x7F) * 0x8000 + (address & 0x7FFF)


def span(rom: bytes, address: int, count: int) -> bytes:
    start = lorom_offset(address)
    if start + count > len(rom):
        raise ValueError(f"ROM range exceeds file: ${address:06X}+{count}")
    return rom[start:start + count]


def word(data: bytes, offset: int = 0) -> int:
    return data[offset] | data[offset + 1] << 8


def descriptor_tiles(rom: bytes, descriptor: int, actor: dict | None = None) -> tuple[bytes, dict]:
    """Recreate $84E6C7's two dynamic graphics-row uploads in local tiles."""
    if not 0x8000 <= descriptor <= 0xFFFF:
        raise ValueError("descriptor must be the 16-bit address stored in object+$14")
    data = span(rom, 0x820000 | descriptor, 6)
    pose = word(data)
    source = data[2] | data[3] << 8 | data[4] << 16
    rows: list[bytes] = []
    for row in range(2):
        header = span(rom, source, 2)
        length = word(header)
        if not length or length > 0x100 or length % 2:
            raise ValueError(f"invalid graphics row {row} for descriptor ${descriptor:04X}")
        rows.append(span(rom, source + 2, length))
        source += 2 + length
    # Each row is DMAed to its native 0x100-word (0x200-byte) region.  Tile
    # indices 0..7 and 16..23 are then addressed by the captured OAM records.
    vram = bytearray(0x600)
    vram[0:len(rows[0])] = rows[0]
    vram[0x200:0x200 + len(rows[1])] = rows[1]
    # $84E77D writes a uniform-detail tile at dynamic tile 23. This is still
    # ROM artwork; the actor fields select its actual variant rather than a
    # browser recolour. Hair type 8 has a separate path and remains capture-
    # gated until its OAM bank is observed.
    detail_source = None
    if actor and actor.get("type", 0) > 1 and actor.get("type") not in (7, 8) and actor.get("uniform_selector") != 0x54:
        detail = data[5]
        if detail & 0x80:
            entry = word(span(rom, 0x81CE8A + actor["uniform_selector"], 2))
            detail_source = entry if entry == 0xF014 else entry + ((detail & 0x7F) - 1) * 32
        elif detail and detail <= 12 and not detail & 1:
            if detail in (4, 6) and actor.get("object_flags", 0) & 0x40:
                detail ^= 2
            entry = word(span(rom, 0x81CEDE + detail, 2))
            detail_source = entry + (actor.get("kit_variant", 0) * 16 if detail < 10 else 0)
        if detail_source is not None and detail_source != 0xF014:
            vram[23 * TILE_BYTES:24 * TILE_BYTES] = span(rom, 0x980000 | detail_source, TILE_BYTES)
    return bytes(vram), {"descriptor": f"${descriptor:04X}", "pose": f"${pose:04X}", "graphics_source": f"${data[4]:02X}{data[3]:02X}{data[2]:02X}", "detail": data[5], "detail_source": None if detail_source is None else f"${detail_source:04X}", "row_bytes": [len(row) for row in rows]}


def decode_tile(vram: bytes, tile: int, palette: list[tuple[int, int, int, int]]) -> Image.Image:
    start = tile * TILE_BYTES
    if start + TILE_BYTES > len(vram):
        return Image.new("RGBA", (8, 8))
    image = Image.new("RGBA", (8, 8))
    pixels = image.load()
    for y in range(8):
        p0, p1, p2, p3 = vram[start + y * 2], vram[start + y * 2 + 1], vram[start + 16 + y * 2], vram[start + 16 + y * 2 + 1]
        for x in range(8):
            bit = 7 - x
            index = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1) | (((p2 >> bit) & 1) << 2) | (((p3 >> bit) & 1) << 3)
            pixels[x, y] = palette[index]
    return image


def tile_at(vram: bytes, tile: int, x: int, y: int, palette: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    actual = tile + (x // 8) + (y // 8) * 16
    tile_image = decode_tile(vram, actual, palette)
    return tile_image.getpixel((x % 8, y % 8))


def parse_palette(values: list[str]) -> list[tuple[int, int, int, int]]:
    if len(values) != 16 or any(not isinstance(value, str) or not value.startswith("#") or len(value) != 7 for value in values):
        raise ValueError("palette must be exactly 16 #RRGGBB values from a ROM kit palette")
    return [(*bytes.fromhex(value[1:]), 0 if index == 0 else 255) for index, value in enumerate(values)]


def parse_palette_banks(capture: dict) -> dict[int, list[tuple[int, int, int, int]]]:
    """Read either one ROM palette or the OAM-indexed banks from one capture."""
    if "palettes" not in capture:
        return {0: parse_palette(capture.get("palette", []))}
    values = capture["palettes"]
    if not isinstance(values, dict):
        raise ValueError("palettes must map captured OBJ palette indexes to 16 colours")
    banks = {}
    for index, palette in values.items():
        try:
            bank = int(index)
        except (TypeError, ValueError) as error:
            raise ValueError("palette-bank index must be an integer") from error
        if not 0 <= bank <= 7:
            raise ValueError("palette-bank index must be in range 0..7")
        banks[bank] = parse_palette(palette)
    if not banks:
        raise ValueError("capture contains no OBJ palette banks")
    return banks


def normalise_parts(parts: list[dict]) -> list[dict]:
    """Accept either the raw SNES property byte or its captured OAM fields."""
    normalised = []
    for part in parts:
        if not {"x", "y", "tile", "size"} <= part.keys():
            raise ValueError("each OAM part requires x, y, tile and size")
        if "attr" in part:
            attr = part["attr"]
        elif {"palette", "priority", "h_flip", "v_flip"} <= part.keys():
            attr = (part["palette"] << 1) | (part["priority"] << 4) | (0x40 if part["h_flip"] else 0) | (0x80 if part["v_flip"] else 0)
        else:
            raise ValueError("each OAM part requires attr or palette, priority, h_flip and v_flip")
        if not isinstance(attr, int) or not 0 <= attr <= 0xFF:
            raise ValueError("OAM attr must be an unsigned byte")
        expected = {"palette": (attr >> 1) & 7, "priority": (attr >> 4) & 3, "h_flip": bool(attr & 0x40), "v_flip": bool(attr & 0x80)}
        for key, value in expected.items():
            if key in part and part[key] != value:
                raise ValueError(f"OAM {key} disagrees with attr")
        normalised.append({**part, "attr": attr, **expected})
    return normalised


def compose(vram: bytes, parts: list[dict], palettes: dict[int, list[tuple[int, int, int, int]]]) -> Image.Image:
    if not parts:
        raise ValueError("capture contains no OAM parts")
    parts = normalise_parts(parts)
    if any(part["tile"] not in range(8) and part["tile"] not in range(16, 24) for part in parts):
        raise ValueError("capture contains a tile outside the player's dynamic VRAM rows")
    left = min(part["x"] for part in parts)
    top = min(part["y"] for part in parts)
    right = max(part["x"] + part["size"] for part in parts)
    bottom = max(part["y"] + part["size"] for part in parts)
    output = Image.new("RGBA", (right - left, bottom - top))
    # The first OAM entry wins.  Drawing in reverse preserves that hardware order.
    for part in reversed(parts):
        size, attr = part["size"], part["attr"]
        if size not in (8, 16):
            raise ValueError("only observed 8x8 and 16x16 player OAM pieces are accepted")
        palette = palettes.get(part["palette"])
        if palette is None:
            raise ValueError(f"capture is missing OBJ palette {part['palette']}")
        for y in range(size):
            for x in range(size):
                sx = size - 1 - x if attr & 0x40 else x
                sy = size - 1 - y if attr & 0x80 else y
                pixel = tile_at(vram, part["tile"], sx, sy, palette)
                if pixel[3]:
                    output.putpixel((part["x"] - left + x, part["y"] - top + y), pixel)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("composition", type=Path, help="same-frame observed player descriptor + OAM JSON")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    capture = json.loads(args.composition.read_text(encoding="utf-8"))
    if capture.get("evidence") != "runtime-oam-capture":
        raise ValueError("composition evidence must be runtime-oam-capture; static coordinates are not accepted")
    descriptor = capture.get("descriptor")
    if not isinstance(descriptor, int):
        raise ValueError("composition requires an integer runtime descriptor")
    palettes = parse_palette_banks(capture)
    vram, descriptor_data = descriptor_tiles(args.rom.read_bytes(), descriptor, capture)
    parts = normalise_parts(capture.get("parts", []))
    image = compose(vram, parts, palettes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    args.output.with_suffix(".json").write_text(json.dumps({"evidence": capture["evidence"], **descriptor_data, "parts": parts, "size": list(image.size)}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
