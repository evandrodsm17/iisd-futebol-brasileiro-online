"""Compare descriptor-upload tile rows against same-frame captured OBJ VRAM."""

import argparse
import importlib.util
import json
from pathlib import Path


def load_renderer():
    path = Path(__file__).with_name("render_issd_descriptor_sprite.py")
    spec = importlib.util.spec_from_file_location("issd_descriptor_renderer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load descriptor renderer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--script", type=lambda value: int(value, 0), required=True)
    args = parser.parse_args()
    renderer = load_renderer()
    rom = args.rom.read_bytes()
    rows = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line]
    rows = [row for row in rows if row["actor"]["animation_script"] == args.script]
    if not rows:
        raise ValueError(f"trace lacks script ${args.script:04X}")

    compared = mismatched = pair_swapped_matches = 0
    details = []
    for row in rows:
        actor, obsel = row["actor"], row["obsel"]
        reconstructed, _ = renderer.descriptor_tiles(rom, actor["descriptor"], actor)
        captured = Path(row["vram"]).read_bytes()
        tile_base = (obsel & 7) << 9
        for tile in sorted({part["tile"] for part in actor["parts"] if part["tile"] in range(8) or part["tile"] in range(16, 24)}):
            expected = reconstructed[tile * 32:(tile + 1) * 32]
            actual = captured[(tile_base + tile) * 32:(tile_base + tile + 1) * 32]
            compared += 1
            swapped = b"".join(actual[index + 1:index + 2] + actual[index:index + 1] for index in range(0, len(actual), 2))
            pair_swapped_matches += swapped == expected
            if actual != expected:
                mismatched += 1
                details.append({
                    "direction": actor["direction"],
                    "descriptor": f"${actor['descriptor']:04X}",
                    "tile": tile,
                    "different_bytes": sum(left != right for left, right in zip(actual, expected)),
                    "first_vram_byte_match": captured.find(expected),
                })
    print(json.dumps({
        "script": f"$82:{args.script:04X}",
        "compared_tiles": compared,
        "mismatched_tiles": mismatched,
        "pair_swapped_matches": pair_swapped_matches,
        "examples": details[:12],
    }, indent=2))


if __name__ == "__main__":
    main()
