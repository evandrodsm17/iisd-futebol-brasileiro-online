"""Export a validated eight-pose ISS Deluxe running cycle from live captures.

The source image data comes from the supplied local ROM; layout and colour
come only from the same-frame OAM/CGRAM observations.  The ROM is never
copied into the output folder.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


CYCLE_BASES = {
    # Values are the first descriptors referenced by the eight direction
    # entries in $82:CF9F (run) and $82:CEF8 (walk), read from the USA ROM.
    "running": ([0xA749, 0xA791, 0xA7D9, 0xA791, 0xA749, 0xA701, 0xA6B9, 0xA701], 8),
    "walking": ([0xA48B, 0xA4E5, 0xA53F, 0xA4E5, 0xA48B, 0xA431, 0xA3D7, 0xA431], 10),
}


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


def read_trace(path: Path) -> tuple[list[dict], list[int]]:
    samples, malformed_lines = [], []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        try:
            samples.append(json.loads(line))
        except json.JSONDecodeError:
            malformed_lines.append(line_number)
    if not samples:
        raise ValueError("trace contains no valid JSONL samples")
    return samples, malformed_lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace", type=Path)
    parser.add_argument("actor_capture", type=Path)
    parser.add_argument("cgram", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--actor", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--cycle", choices=CYCLE_BASES, default="running")
    parser.add_argument("--direction", type=int, choices=range(8), default=0)
    args = parser.parse_args()

    renderer = load_renderer()
    rom = args.rom.read_bytes()
    trace, malformed_lines = read_trace(args.trace)
    if malformed_lines:
        print(f"warning: ignored malformed trace lines {malformed_lines}", file=sys.stderr)
    captured = json.loads(args.actor_capture.read_text(encoding="utf-8"))
    if captured.get("evidence") != "runtime-oam-capture":
        raise ValueError("actor capture must be runtime-oam-capture evidence")
    context = next((actor for actor in captured["actors"] if actor["object"] == f"0x{args.actor:04X}"), None)
    # The live trace carries these fields too. It is the authoritative fallback
    # for an actor allocated after the one-frame composition capture.
    if context is None:
        observed_actor = next((actor for sample in trace for actor in sample["actors"] if actor["address"] == args.actor), None)
        if observed_actor is None:
            raise ValueError("selected actor is absent from both actor capture and trace")
        context = observed_actor

    base, length = CYCLE_BASES[args.cycle]
    descriptors = [base[args.direction] + index * 9 for index in range(length)]
    observed = {}
    for sample in trace:
        for actor in sample["actors"]:
            descriptor = actor["descriptor"]
            if (actor["address"] == args.actor and actor["direction"] == args.direction
                    and descriptor in descriptors and descriptor not in observed):
                observed[descriptor] = (sample["frame"], actor)
    missing = [f"${descriptor:04X}" for descriptor in descriptors if descriptor not in observed]
    if missing:
        raise ValueError("trace lacks a complete observed cycle: " + ", ".join(missing))

    palettes = renderer.parse_palette_banks({"palettes": cgram_banks(args.cgram)})
    images, metadata = [], []
    for descriptor in descriptors:
        sample_frame, actor = observed[descriptor]
        tiles, descriptor_data = renderer.descriptor_tiles(rom, descriptor, context)
        parts = renderer.normalise_parts(actor["parts"])
        image = renderer.compose(tiles, parts, palettes)
        images.append(image)
        metadata.append({
            "sample_frame": sample_frame,
            "descriptor": f"${descriptor:04X}",
            "pose": f"${actor['pose']:04X}",
            "direction": actor["direction"],
            "descriptor_data": descriptor_data,
            "parts": parts,
            "image_size": list(image.size),
        })

    cell_width = max(image.width for image in images) + 4
    cell_height = max(image.height for image in images) + 4
    sheet = Image.new("RGBA", (cell_width * len(images), cell_height), (0, 0, 0, 0))
    for index, image in enumerate(images):
        sheet.alpha_composite(image, (index * cell_width + (cell_width - image.width) // 2, cell_height - image.height - 2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    args.output.with_suffix(".json").write_text(json.dumps({
        "evidence": "runtime-oam-capture",
        "actor": f"0x{args.actor:04X}",
        "cycle": args.cycle,
        "direction": args.direction,
        "palette_source": str(args.cgram),
        "ignored_trace_lines": malformed_lines,
        "frames": metadata,
        "sheet_size": list(sheet.size),
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
