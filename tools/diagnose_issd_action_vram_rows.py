"""Compare captured dynamic VRAM against descriptor rows when context exists."""

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

    if not all("object_field_02" in row["actor"] for row in rows):
        print(json.dumps({
            "script": f"$82:{args.script:04X}",
            "compared_tiles": 0,
            "status": "legacy-trace-without-object-field-02",
            "reason": "The trace predates the collector field required by the reference-assisted formula.",
        }, indent=2))
        return

    compared = mismatched = 0
    examples = []
    for row in rows:
        actor = row["actor"]
        reconstructed, _ = renderer.descriptor_tiles(rom, actor["descriptor"], actor)
        captured = Path(row["vram"]).read_bytes()
        # The same formula appears in CODE_84:E6C7 and in the independently
        # reviewed native reference.  It remains a hypothesis until this tool
        # reports a byte match on a fresh local-ROM capture.
        base = (0x6000 + ((actor["object_field_02"] & 0x01FF) << 4)) * 2
        for tile in sorted({part["tile"] for part in actor["parts"] if part["tile"] in range(8) or part["tile"] in range(16, 24)}):
            expected = reconstructed[tile * 32:(tile + 1) * 32]
            actual = captured[base + tile * 32:base + (tile + 1) * 32]
            compared += 1
            if actual != expected:
                mismatched += 1
                examples.append({"descriptor": f"${actor['descriptor']:04X}", "direction": actor["direction"], "tile": tile,
                                 "different_bytes": sum(left != right for left, right in zip(actual, expected))})
    print(json.dumps({
        "script": f"$82:{args.script:04X}",
        "status": "reference-assisted-formula-tested",
        "formula": "$6000 + ((object_field_02 & $01FF) << 4) VRAM words",
        "compared_tiles": compared,
        "mismatched_tiles": mismatched,
        "examples": examples[:12],
    }, indent=2))


if __name__ == "__main__":
    main()
