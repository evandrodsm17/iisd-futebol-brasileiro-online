#!/usr/bin/env python3
"""Extract the original ISSD national-flag sprite resources from a USA ROM.

The cartridge stores these as Konami LZSS/RLE streams and reuses an indexed
shape for flags with the same geometry (for example vertical tricolours).  It
then selects each nation's four-colour palette at runtime.  This exporter
keeps those two facts explicit: every generated PNG is derived from the ROM,
and its manifest preserves the source stream and palette addresses.

It exports the two named sprite halves exactly as the disassembly labels them,
plus their verified 24x16 vertical composite.  The half names are literal: the
two streams share width and stack without overlap, so the composite does not
infer any placement outside the cartridge data.

Usage:
  python tools/extract_issd_flags.py ROM.sfc OUTPUT_DIRECTORY
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


EXPECTED_MD5 = "345ddedcd63412b9373dabb67c11fc05"
TILE_BYTES = 32
TILE = 8
TILES_PER_ROW = 3

# Cartridge teams are ordered by their roster-table ID.  Entries sharing a
# source have a common flag silhouette but retain an independent palette.
TEAMS = (
    ("italy", "Italy", "ItalyFranceIrelandBelgiumRomaniaNigeria", 0x89963E),
    ("holland", "Holland", "GermanyHollandRussia", 0x899648),
    ("england", "England", "EnglandNorwaySwedenDenmark", 0x8996D4),
    ("norway", "Norway", "EnglandNorwaySwedenDenmark", 0x899684),
    ("spain", "Spain", "Spain", 0x899742),
    ("ireland", "Ireland", "ItalyFranceIrelandBelgiumRomaniaNigeria", 0x89968E),
    ("portugal", "Portugal", "Portugal", 0x899760),
    ("denmark", "Denmark", "EnglandNorwaySwedenDenmark", 0x899698),
    ("germany", "Germany", "GermanyHollandRussia", 0x899634),
    ("france", "France", "ItalyFranceIrelandBelgiumRomaniaNigeria", 0x8996A2),
    ("belgium", "Belgium", "ItalyFranceIrelandBelgiumRomaniaNigeria", 0x89967A),
    ("sweden", "Sweden", "EnglandNorwaySwedenDenmark", 0x899670),
    ("romania", "Romania", "ItalyFranceIrelandBelgiumRomaniaNigeria", 0x899652),
    ("bulgaria", "Bulgaria", "Bulgaria", 0x8996E8),
    ("russia", "Russia", "GermanyHollandRussia", 0x89965C),
    ("swiss", "Swiss", "Switzerland", 0x899792),
    ("greece", "Greece", "Greece", 0x899788),
    ("croatia", "Croatia", "Croatia", 0x89979C),
    ("austria", "Austria", "Austria", 0x89974C),
    ("wales", "Wales", "Wales", 0x89971A),
    ("scotland", "Scotland", "Scotland", 0x89977E),
    ("northern-ireland", "N.Ireland", "NorthIreland", 0x899710),
    ("czech-republic", "Czech Rep.", "CzechRepublic", 0x899738),
    ("poland", "Poland", "Poland", 0x899774),
    ("japan", "Japan", "Japan", 0x899756),
    ("south-korea", "S.Korea", "SouthKorea", 0x8996CA),
    ("turkey", "Turkey", "Turkey", 0x8996FC),
    ("nigeria", "Nigeria", "ItalyFranceIrelandBelgiumRomaniaNigeria", 0x899666),
    ("cameroon", "Cameroon", "Cameroon", 0x8996F2),
    ("morocco", "Morocco", "Morocco", 0x89976A),
    ("brazil", "Brazil", "Brazil", 0x89972E),
    ("argentina", "Argentina", "Argentina", 0x8996C0),
    ("columbia", "Columbia", "Columbia", 0x899706),
    ("mexico", "Mexico", "Mexico", 0x8996B6),
    ("usa", "U.S.A", "USA", 0x8996DE),
    ("uruguay", "Uruguay", "Uruguay", 0x899724),
)

# Direct CPU addresses recorded in AssetPointersAndFiles.asm.  Keeping them
# here makes the tool reproducible without requiring the disassembly folder.
STREAMS = {
    "GermanyHollandRussia": (0xA7E4B6, 0xA7E4C2),
    "ItalyFranceIrelandBelgiumRomaniaNigeria": (0xA7E4CF, 0xA7E4D9),
    "EnglandNorwaySwedenDenmark": (0xA7E4E3, 0xA7E4FF),
    "Mexico": (0xA7E518, 0xA7E529), "SouthKorea": (0xA7E53C, 0xA7E562),
    "USA": (0xA7E58A, 0xA7E5A3), "Cameroon": (0xA7E5AF, 0xA7E5C6),
    "Columbia": (0xA7E5DC, 0xA7E5E8), "Wales": (0xA7E5F1, 0xA7E621),
    "Brazil": (0xA7E64E, 0xA7E66F), "Spain": (0xA7E692, 0xA7E6AF),
    "Argentina": (0xA7E6C8, 0xA7E6D7), "Japan": (0xA7E6E8, 0xA7E706),
    "Bulgaria": (0xA7E71F, 0xA7E72B), "Morocco": (0xA7E737, 0xA7E74A),
    "Turkey": (0xA7E759, 0xA7E779), "NorthIreland": (0xA7E799, 0xA7E7CB),
    "Uruguay": (0xA7E801, 0xA7E81E), "CzechRepublic": (0xA7E82B, 0xA7E845),
    "Austria": (0xA7E858, 0xA7E864), "Portugal": (0xA7E86D, 0xA7E88D),
    "Poland": (0xA7E8A8, 0xA7E8B1), "Greece": (0xA7E8B9, 0xA7E8E1),
    "Switzerland": (0xA7E8F6, 0xA7E91A), "Scotland": (0xA7E99C, 0xA7E9D0),
    "Croatia": (0xA7EA06, 0xA7EA2C),
}


def strip_copier_header(data: bytes) -> bytes:
    return data[512:] if len(data) % 1024 == 512 else data


def lorom_offset(address: int) -> int:
    return ((address >> 16) & 0x7F) * 0x8000 + (address & 0x7FFF)


def bgr555(value: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(
        (value & 31) * 255 // 31, ((value >> 5) & 31) * 255 // 31,
        ((value >> 10) & 31) * 255 // 31,
    )


def decompress(rom: bytes, address: int) -> tuple[bytes, bool]:
    """Decode the ROM's Konami LZSS/RLE resource format."""
    position = lorom_offset(address)
    header = int.from_bytes(rom[position:position + 2], "little")
    end = position + (header & 0x7FFF)
    if end <= position + 2 or end > len(rom):
        raise ValueError(f"invalid compressed range at ${address:06X}")
    position += 2
    window, cursor, output = bytearray(1024), 0, bytearray()

    def read() -> int:
        nonlocal position
        if position >= end:
            raise ValueError(f"truncated command at ${address:06X}")
        value = rom[position]
        position += 1
        return value

    def emit(value: int) -> None:
        nonlocal cursor
        output.append(value)
        window[cursor] = value
        cursor = (cursor + 1) & 0x3FF

    while position < end:
        command = read()
        if command < 0x80:
            reference = ((((command & 3) << 8) | read()) - 0x3DF) & 0x3FF
            for _ in range((command >> 2) + 2):
                emit(window[reference])
                reference = (reference + 1) & 0x3FF
        elif command < 0xA0:
            for _ in range(command & 31):
                emit(read())
        elif command < 0xC0:
            for _ in range((command & 31) + 2):
                emit(0)
                emit(read())
        elif command < 0xE0:
            value = read()
            for _ in range((command & 31) + 2):
                emit(value)
        else:
            count = read() + 2 if command == 0xFF else (command & 31) + 2
            for _ in range(count):
                emit(0)
    return bytes(output), bool(header & 0x8000)


def deinterleave_tiles(data: bytes) -> bytes:
    if len(data) % 16:
        raise ValueError("interleaved tile data is not 16-byte aligned")
    output = bytearray()
    for start in range(0, len(data), 16):
        first, second = data[start:start + 8], data[start + 8:start + 16]
        output.extend(value for pair in zip(first, second) for value in pair)
    return bytes(output)


def render(data: bytes, palette: list[str]) -> Image.Image:
    if len(data) % TILE_BYTES:
        raise ValueError("sprite data is not made of 4bpp SNES tiles")
    tile_count = len(data) // TILE_BYTES
    if not tile_count or tile_count % TILES_PER_ROW:
        raise ValueError(f"flag stream is not a full 24-pixel tile row ({tile_count} tiles)")
    image = Image.new("RGBA", (TILES_PER_ROW * TILE, (tile_count // TILES_PER_ROW) * TILE))
    pixels = image.load()
    colours = [(0, 0, 0, 0)] + [tuple(bytes.fromhex(value[1:]) + b"\xff") for value in palette[1:]]
    for tile_index in range(tile_count):
        start = tile_index * TILE_BYTES
        origin_x, origin_y = (tile_index % TILES_PER_ROW) * TILE, (tile_index // TILES_PER_ROW) * TILE
        for y in range(TILE):
            planes = (data[start + y * 2], data[start + y * 2 + 1], data[start + 16 + y * 2], data[start + 16 + y * 2 + 1])
            for x in range(TILE):
                bit = 7 - x
                index = sum(((plane >> bit) & 1) << shift for shift, plane in enumerate(planes))
                # Flag streams use OBJ colours 12..15.  Values outside the
                # flag range are transparent, never substituted with a guess.
                pixels[origin_x + x, origin_y + y] = colours[index - 12] if index >= 12 else (0, 0, 0, 0)
    return image


def palette(rom: bytes, address: int) -> list[str]:
    offset = lorom_offset(address)
    return [bgr555(int.from_bytes(rom[offset + index:offset + index + 2], "little")) for index in range(0, 8, 2)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = strip_copier_header(args.rom.read_bytes())
    digest = hashlib.md5(rom).hexdigest()
    if digest != EXPECTED_MD5:
        raise SystemExit(f"ROM MD5 {digest}; expected USA ROM {EXPECTED_MD5}")

    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"rom_md5": digest, "format": "SNES 4bpp indexed sprites", "teams": []}
    for slug, name, stream_name, palette_address in TEAMS:
        top_address, bottom_address = STREAMS[stream_name]
        colours = palette(rom, palette_address)
        entry = {"id": slug, "name": name, "palette_source": f"${palette_address:06X}", "palette": colours, "parts": []}
        for part, address in (("top", top_address), ("bottom", bottom_address)):
            data, interleaved = decompress(rom, address)
            if interleaved:
                data = deinterleave_tiles(data)
            output_name = f"{slug}-{part}.png"
            render(data, colours).save(args.output / output_name)
            entry["parts"].append({"name": part, "file": output_name, "source": f"${address:06X}", "decoded_bytes": len(data)})
        top = Image.open(args.output / entry["parts"][0]["file"])
        bottom = Image.open(args.output / entry["parts"][1]["file"])
        if top.width != bottom.width:
            raise ValueError(f"{name} flag halves have incompatible widths")
        composite = Image.new("RGBA", (top.width, top.height + bottom.height))
        composite.alpha_composite(top, (0, 0))
        composite.alpha_composite(bottom, (0, top.height))
        entry["file"] = f"{slug}.png"
        composite.save(args.output / entry["file"])
        manifest["teams"].append(entry)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(manifest['teams'])} team flag records to {args.output}")


if __name__ == "__main__":
    main()
