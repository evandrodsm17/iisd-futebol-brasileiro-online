"""Render action OAM records using their matching full VRAM and CGRAM dumps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from render_issd_oam_composite import color, decode_tile


def render(record: dict) -> Image.Image:
    actor, obsel = record["actor"], record["obsel"]
    vram = Path(record["vram"]).read_bytes()
    cgram = bytes.fromhex("".join(Path(record["cgram"]).read_text(encoding="utf-8").split()))
    if len(vram) != 0x10000 or len(cgram) != 0x200:
        raise ValueError("capture must contain 64 KiB VRAM and 512-byte CGRAM")
    parts = actor["parts"]
    left, top = min(part["x"] for part in parts), min(part["y"] for part in parts)
    right = max(part["x"] + part["size"] for part in parts)
    bottom = max(part["y"] + part["size"] for part in parts)
    image = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    for part in reversed(parts):
        attr, size = part["attr"], part["size"]
        tile_base = (obsel & 7) << 9
        if attr & 1:
            tile_base += ((obsel & 0x18) + 8) << 5
        palette = (attr >> 1) & 7
        for y in range(size):
            for x in range(size):
                sx = size - 1 - x if attr & 0x40 else x
                sy = size - 1 - y if attr & 0x80 else y
                tile = (part["tile"] & 0xF0) | ((part["tile"] + (sx >> 3)) & 0x0F)
                value = decode_tile(vram, tile_base + tile + 16 * (sy >> 3))[sy & 7][sx & 7]
                if value:
                    image.putpixel((part["x"] - left + x, part["y"] - top + y), color(cgram, palette * 16 + value))
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError("trace contains no action snapshots")
    images = [render(row) for row in rows]
    cell_w, cell_h = max(i.width for i in images) + 4, max(i.height for i in images) + 4
    sheet = Image.new("RGBA", (cell_w * len(images), cell_h), (0, 0, 0, 0))
    for index, image in enumerate(images):
        sheet.alpha_composite(image, (index * cell_w + (cell_w - image.width) // 2, cell_h - image.height - 2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)


if __name__ == "__main__":
    main()
