"""Verify ROM descriptor reconstruction against same-frame action VRAM captures."""

import argparse
import importlib.util
import json
from pathlib import Path


def load_module(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def palette_banks(path: Path) -> dict[str, list[str]]:
    data = bytes.fromhex("".join(path.read_text(encoding="utf-8").split()))
    if len(data) != 0x200:
        raise ValueError("CGRAM capture must contain exactly 512 bytes")
    banks: dict[str, list[str]] = {}
    for bank in range(8):
        colors = []
        for index in range(16):
            value = data[(bank * 16 + index) * 2] | data[(bank * 16 + index) * 2 + 1] << 8
            colors.append("#%02X%02X%02X" % (
                (value & 0x1F) * 255 // 31,
                ((value >> 5) & 0x1F) * 255 // 31,
                ((value >> 10) & 0x1F) * 255 // 31,
            ))
        banks[str(bank)] = colors
    return banks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--script", type=lambda value: int(value, 0), required=True)
    args = parser.parse_args()

    action_renderer = load_module("render_issd_action_vram_capture.py")
    descriptor_renderer = load_module("render_issd_descriptor_sprite.py")
    rom = args.rom.read_bytes()
    rows = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line]
    rows = [row for row in rows if row["actor"]["animation_script"] == args.script]
    if not rows:
        raise ValueError(f"trace lacks script ${args.script:04X}")

    mismatches = []
    for row in rows:
        actor = row["actor"]
        tiles, _ = descriptor_renderer.descriptor_tiles(rom, actor["descriptor"], actor)
        palettes = descriptor_renderer.parse_palette_banks({"palettes": palette_banks(Path(row["cgram"]))})
        reconstructed = descriptor_renderer.compose(tiles, actor["parts"], palettes)
        captured = action_renderer.render(row)
        if reconstructed.size != captured.size or reconstructed.tobytes() != captured.tobytes():
            mismatches.append({
                "direction": actor["direction"],
                "descriptor": f"${actor['descriptor']:04X}",
                "captured_size": list(captured.size),
                "reconstructed_size": list(reconstructed.size),
            })
    if mismatches:
        raise SystemExit(f"action descriptor mismatch for {len(mismatches)} pose(s): {mismatches}")
    print(f"action descriptor capture: OK ({len(rows)} poses for ${args.script:04X})")


if __name__ == "__main__":
    main()
