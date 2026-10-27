"""Export connected on-field OAM groups from an ISSD match snapshot.

Each resulting PNG contains only the composition produced by the captured
retail OAM, VRAM and CGRAM state.  HUD and minimap slots are excluded before
grouping; the contact sheet is a validation artifact, not a browser asset.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from render_issd_oam_composite import color, decode_tile


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "issd-oam-groups"
OBJSEL = 0x03
SIZES = ((8, 16), (8, 32), (8, 64), (16, 32), (16, 64), (32, 64), (16, 32), (16, 32))


def load_entries() -> list[dict]:
    raw = bytes.fromhex("".join(DOCS.joinpath("issd-runtime-oam.hex").read_text(encoding="utf-8").split()))
    raw = raw[:512][::-1] + raw[512:]
    entries = []
    for slot in range(128):
        x, y, tile, props = raw[slot * 4:slot * 4 + 4]
        high = (raw[512 + slot // 4] >> ((slot % 4) * 2)) & 3
        if x == y == tile == props == 0xF0:
            continue
        if high & 1:
            x -= 512
        size = SIZES[OBJSEL >> 5][high >> 1]
        # Original HUD and radar retain their canonical screen positions.
        if y < 32 or (88 <= x < 168 and 160 <= y < 216):
            continue
        if x + size <= 0 or x >= 256 or y >= 224:
            continue
        entries.append({"slot": slot, "x": x, "y": y, "tile": tile, "props": props, "size": size})
    return entries


def components(entries: list[dict]) -> list[list[dict]]:
    parent = list(range(len(entries)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(left: int, right: int) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for left, a in enumerate(entries):
        for right, b in enumerate(entries[left + 1:], left + 1):
            # Fifteen-pixel slack joins the related 8x8/16x16 layers of one
            # actor while leaving players at normal field separation apart.
            if not (a["x"] + a["size"] + 15 < b["x"] or b["x"] + b["size"] + 15 < a["x"] or
                    a["y"] + a["size"] + 15 < b["y"] or b["y"] + b["size"] + 15 < a["y"]):
                join(left, right)
    grouped: dict[int, list[dict]] = {}
    for index, entry in enumerate(entries):
        grouped.setdefault(find(index), []).append(entry)
    return sorted(grouped.values(), key=lambda group: (min(entry["y"] for entry in group), min(entry["x"] for entry in group)))


def render(group: list[dict], vram: bytes, cgram: bytes) -> tuple[Image.Image, dict]:
    left = min(entry["x"] for entry in group)
    top = min(entry["y"] for entry in group)
    right = max(entry["x"] + entry["size"] for entry in group)
    bottom = max(entry["y"] + entry["size"] for entry in group)
    image = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    # Lower OAM slots are in front, so draw in reverse slot order.
    for entry in sorted(group, key=lambda item: item["slot"], reverse=True):
        props, tile, size = entry["props"], entry["tile"], entry["size"]
        tile_base = (OBJSEL & 7) << 9
        if props & 1:
            tile_base += ((OBJSEL & 0x18) + 8) << 5
        palette = (props >> 1) & 7
        for sy in range(size):
            for sx in range(size):
                px = size - 1 - sx if props & 0x40 else sx
                py = size - 1 - sy if props & 0x80 else sy
                tile_number = (tile & 0xF0) | ((tile + (px >> 3)) & 0x0F)
                tile_number += 16 * (py >> 3)
                value = decode_tile(vram, tile_base + tile_number)[py & 7][px & 7]
                if value:
                    image.putpixel((entry["x"] - left + sx, entry["y"] - top + sy), color(cgram, palette * 16 + value))
    metadata = {"slots": [entry["slot"] for entry in group], "bounds": [left, top, right, bottom]}
    return image, metadata


def main() -> None:
    OUT.mkdir(exist_ok=True)
    vram = DOCS.joinpath("issd-runtime-vram.bin").read_bytes()
    cgram = bytes.fromhex("".join(DOCS.joinpath("issd-runtime-cgram.hex").read_text(encoding="utf-8").split()))
    groups = components(load_entries())
    metadata = []
    previews = []
    for index, group in enumerate(groups):
        image, data = render(group, vram, cgram)
        filename = f"group-{index:02d}.png"
        image.save(OUT / filename)
        data["file"] = filename
        metadata.append(data)
        preview = Image.new("RGBA", (max(48, image.width), max(64, image.height)), (20, 80, 52, 255))
        preview.alpha_composite(image, ((preview.width - image.width) // 2, (preview.height - image.height) // 2))
        previews.append((preview.convert("RGB"), data))
    DOCS.joinpath("issd-oam-groups.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    sheet = Image.new("RGB", (192 * 4, 96 * max(1, (len(previews) + 3) // 4)), "black")
    painter = ImageDraw.Draw(sheet)
    for index, (preview, data) in enumerate(previews):
        x, y = (index % 4) * 192, (index // 4) * 96
        preview.thumbnail((180, 72), Image.Resampling.NEAREST)
        sheet.paste(preview, (x + (192 - preview.width) // 2, y + 20))
        painter.text((x + 4, y + 4), f"group {index}: {data['slots']}", fill="white")
    sheet.save(DOCS / "issd-oam-groups.png")


if __name__ == "__main__":
    main()
