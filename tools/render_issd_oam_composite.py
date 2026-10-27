"""Render a diagnostic composite from one ISSD runtime OAM/VRAM/CGRAM capture.

This is intentionally an evidence tool, not a production asset exporter.  It
turns the four OAM work planes built by ISSD into 8x8 SNES OBJ tiles using the
same frame's VRAM and palette mirror, making incorrect tile-base assumptions
visible before any browser sprite is replaced.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


WIDTH, HEIGHT = 512, 224


def decode_tile(vram: bytes, tile: int) -> list[list[int]]:
    """Decode one 4bpp SNES tile from the OBJ tile-number address space."""
    start = (tile & 0x1FF) * 32
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0, p1 = vram[start + y * 2:start + y * 2 + 2]
        p2, p3 = vram[start + 16 + y * 2:start + 16 + y * 2 + 2]
        for x in range(8):
            bit = 7 - x
            pixels[y][x] = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1) | (((p2 >> bit) & 1) << 2) | (((p3 >> bit) & 1) << 3)
    return pixels


def color(cgram: bytes, index: int) -> tuple[int, int, int, int]:
    word = cgram[index * 2] | (cgram[index * 2 + 1] << 8)
    # SNES CGRAM is BGR555.  Zero in a sprite tile is transparent.
    return ((word & 31) * 255 // 31, ((word >> 5) & 31) * 255 // 31, ((word >> 10) & 31) * 255 // 31, 255)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("planes", type=Path)
    parser.add_argument("vram", type=Path)
    parser.add_argument("cgram", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--obsel", type=lambda value: int(value, 0), default=0,
                        help="captured SNES OBJSEL register (default: 0)")
    args = parser.parse_args()

    source_lines = [line.strip() for line in args.planes.read_text(encoding="utf-8").splitlines() if line.strip()]
    source = bytes.fromhex("".join(source_lines))
    vram = args.vram.read_bytes()
    cgram = bytes.fromhex("".join(args.cgram.read_text(encoding="utf-8").split()))
    if len(vram) != 0x10000 or len(cgram) != 0x200:
        raise ValueError("expected 64 KiB VRAM and 512-byte CGRAM captures")

    image = Image.new("RGBA", (WIDTH, HEIGHT), (20, 80, 52, 255))
    if len(source) == 544:
        # The retail OAM mirror is 128 contiguous 4-byte entries, followed by
        # 32 high-X/size bytes.  This is the documented $0001E0 buffer.
        # ISSD's DMA sends the low OAM buffer from $03DF down to $01E0.
        # Its final high-OAM 32-byte transfer remains forward ordered.
        source = source[:512][::-1] + source[512:]
        entries = []
        for slot in range(128):
            x, y, tile, props = source[slot * 4:slot * 4 + 4]
            high = (source[512 + slot // 4] >> ((slot % 4) * 2)) & 3
            if x == y == tile == props == 0xF0:
                continue
            entries.append((x | ((high & 1) << 8), y, tile, props))
    else:
        planes = [bytes.fromhex(line) for line in source_lines]
        if len(planes) != 4 or any(len(plane) != 256 for plane in planes):
            raise ValueError("expected final 544-byte OAM buffer or four 256-byte work planes")
        entries = [tuple(plane[slot] for plane in planes) for slot in range(256)]

    object_sizes = ((8, 16), (8, 32), (8, 64), (16, 32),
                    (16, 64), (32, 64), (16, 32), (16, 32))
    for slot, (x, y, tile, props) in enumerate(entries):
        # ISSD clears inactive OAM entries to $F0.
        if x == y == tile == props == 0xF0:
            continue
        high = 0
        if len(source) == 544:
            high = (source[512 + slot // 4] >> ((slot % 4) * 2)) & 3
        size = object_sizes[(args.obsel >> 5) & 7][(high >> 1) & 1]
        # PPU_objTileAdr* are expressed in 16-bit VRAM words; one 4bpp tile
        # occupies 16 words, hence the conversion to tile units below.
        tile_base = ((args.obsel & 7) << 9) + (((args.obsel & 0x18) + 8) << 5 if props & 1 else 0)
        palette = (props >> 1) & 7
        for sy in range(size):
            for sx in range(size):
                source_x = 7 - sx if props & 0x40 else sx
                source_y = 7 - sy if props & 0x80 else sy
                # SNES OBJ tiles advance horizontally within each 16-tile row.
                tile_number = (tile & 0xF0) | ((tile + (source_x >> 3)) & 0x0F)
                tile_number += 16 * (source_y >> 3)
                pixels = decode_tile(vram, tile_base + tile_number)
                palette_index = pixels[source_y & 7][source_x & 7]
                if not palette_index:
                    continue
                dx, dy = x + sx, y + sy
                if 0 <= dx < WIDTH and 0 <= dy < HEIGHT:
                    image.putpixel((dx, dy), color(cgram, palette * 16 + palette_index))
    image.save(args.output)


if __name__ == "__main__":
    main()
