"""Render distinct action poses only from matching runtime OAM/CGRAM evidence."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from PIL import Image


def load_renderer():
    path = Path(__file__).with_name("render_issd_descriptor_sprite.py")
    spec = importlib.util.spec_from_file_location("issd_descriptor_renderer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load descriptor renderer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cgram_banks(path: Path) -> dict[str, list[str]]:
    data = bytes.fromhex("".join(path.read_text(encoding="utf-8").split()))
    if len(data) != 0x200:
        raise ValueError("CGRAM capture must contain exactly 512 bytes")

    def colour(index: int) -> str:
        value = data[index * 2] | data[index * 2 + 1] << 8
        return "#%02X%02X%02X" % (
            (value & 0x1F) * 255 // 31,
            ((value >> 5) & 0x1F) * 255 // 31,
            ((value >> 10) & 0x1F) * 255 // 31,
        )

    return {str(bank): [colour(bank * 16 + index) for index in range(16)] for bank in range(8)}


def samples(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"malformed JSONL at line {line_number}") from error
    if not rows:
        raise ValueError("trace contains no samples")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace", type=Path)
    parser.add_argument("cgram", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--script", type=lambda value: int(value, 0), required=True)
    args = parser.parse_args()

    renderer = load_renderer()
    palettes = renderer.parse_palette_banks({"palettes": cgram_banks(args.cgram)})
    unique: dict[tuple[int, int], tuple[int, dict]] = {}
    for sample in samples(args.trace):
        for actor in sample.get("actors", []):
            if actor.get("animation_script") != args.script or not actor.get("parts"):
                continue
            key = actor["direction"], actor["descriptor"]
            unique.setdefault(key, (sample["frame"], actor))
    if not unique:
        raise ValueError(f"trace lacks OAM parts for script ${args.script:04X}")

    allowed_tiles = set(range(8)) | set(range(16, 24))
    blockers = []
    for (direction, descriptor), (frame, actor) in sorted(unique.items()):
        unsupported = sorted({part["tile"] for part in actor["parts"] if part["tile"] not in allowed_tiles})
        if unsupported:
            blockers.append({
                "frame": frame,
                "direction": direction,
                "descriptor": f"${descriptor:04X}",
                "actor": f"0x{actor['address']:04X}",
                "unsupported_tiles": unsupported,
                "reason": "matching frame VRAM was not captured for tiles outside the dynamic player rows",
            })
    if blockers:
        args.output.with_suffix(".json").write_text(json.dumps({
            "evidence": "runtime-oam-capture",
            "trace": str(args.trace),
            "cgram": str(args.cgram),
            "script": f"$82:{args.script:04X}",
            "rendered": False,
            "blockers": blockers,
            "limitations": "No partial PNG was emitted; unsupported OAM tiles require same-frame VRAM.",
        }, indent=2) + "\n", encoding="utf-8")
        print(f"action render blocked: {len(blockers)} poses require same-frame VRAM")
        return

    frames = []
    for (direction, descriptor), (frame, actor) in sorted(unique.items()):
        tiles, descriptor_data = renderer.descriptor_tiles(args.rom.read_bytes(), descriptor, actor)
        parts = renderer.normalise_parts(actor["parts"])
        image = renderer.compose(tiles, parts, palettes)
        frames.append({
            "frame": frame,
            "direction": direction,
            "descriptor": f"${descriptor:04X}",
            "pose": f"${actor['pose']:04X}",
            "actor": f"0x{actor['address']:04X}",
            "image": image,
            "parts": parts,
            "descriptor_data": descriptor_data,
        })

    cell_w = max(frame["image"].width for frame in frames) + 4
    cell_h = max(frame["image"].height for frame in frames) + 4
    sheet = Image.new("RGBA", (cell_w * len(frames), cell_h), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        image = frame.pop("image")
        sheet.alpha_composite(image, (index * cell_w + (cell_w - image.width) // 2, cell_h - image.height - 2))
        frame["image_size"] = list(image.size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    args.output.with_suffix(".json").write_text(json.dumps({
        "evidence": "runtime-oam-capture",
        "trace": str(args.trace),
        "cgram": str(args.cgram),
        "script": f"$82:{args.script:04X}",
        "frames": frames,
        "sheet_size": list(sheet.size),
        "limitations": "Observed poses only; this is not a complete action animation.",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
