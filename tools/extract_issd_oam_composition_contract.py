"""Extract the native ISSD object-to-OAM composition contract from assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, length: int) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + length])


def require(text: str, label: str, *needles: str) -> None:
    for needle in needles:
        if needle not in text:
            raise ValueError(f"{label} no longer contains {needle}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    builder = block(lines, "CODE_8095E0", 225)
    dynamic = block(lines, "CODE_8096DB", 80)
    require(builder, "CODE_80:95E0",
            "LDY.w #$1D40", "LDA.b $08,x", "LDA.b $0C,x", "ADC.b $10,x",
            "LDA.b $02,x", "LDA.b $05,x", "ORA.b $04,x")
    require(dynamic, "CODE_80:96DB",
            "LDA.b $00,x", "STA.b $FA", "LDA.w $0004,x", "JMP.w CODE_809663",
            "INX", "DEC.b $FA")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:95E0"},
        "draw_list": {
            "base": "$7E:1D40",
            "terminator": "zero object pointer",
            "ordering": "the list is consumed sequentially; its producer/sort remains a separate contract",
        },
        "object_transform": {
            "x_origin": "object+$08",
            "y_origin": "object+$0C + object+$10",
            "tile_base": "object+$02 is added to each geometry tile before hardware OAM write",
            "attributes": "object+$03, inherited palette bits from object+$05 or $7E:007C, and object+$04 are combined before per-part XOR/flip handling",
        },
        "dynamic_geometry": {
            "pose_pointer": "object+$00 points to a count-prefixed runtime geometry record",
            "part_arrays": "$7E:2000 (x), $7E:4000 (y), $7E:6000 (tile/attributes), indexed from the pose pointer",
            "tile_normalization": "geometry_tile is pre-base; tile is the final OAM byte after object+$02",
        },
        "visibility": {
            "x": "native builder rejects parts outside its signed horizontal bounds before OAM emission",
            "y": "native builder rejects parts outside its signed vertical bounds before OAM emission",
            "note": "exact branch thresholds are preserved in CODE_80:9663/CODE_80:96FE; callers must not replace this with arbitrary browser clipping when validating native output",
        },
        "limitations": [
            "This extract proves composition mechanics, not the semantic identity of every object in the draw list.",
            "Static packed geometry and runtime dynamic geometry use distinct branches and must not be conflated.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
