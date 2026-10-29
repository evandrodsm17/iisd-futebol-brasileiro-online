"""Extract the update and transition contract of collision-machine state 1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 52) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + count])


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
    state1 = block(lines, "CODE_83D82C", 57)
    bounds = block(lines, "CODE_83D854", 22)
    require(state1, "CODE_83:D82C", "DEC.b $08", "DEC.b $0C", "JSR.w CODE_83D854", "LDX.w $00C6", "LDA.w $000C,x", "SBC.w #$0010", "CMP.b $0C", "BPL.b CODE_83D873", "JSL.l CODE_84E894", "LDY.b $1A", "LDA.w DATA_81B03D,y", "STA.w $07A0", "LDA.w DATA_81B031,y", "STA.w $08A0", "CODE_83D873:", "INC.b $32", "LDA.w #DATA_82ED71", "LDY.w #DATA_82ED77", "JSL.l CODE_84E89C")
    require(bounds, "CODE_83:D854", "LDA.b $08", "ADC.w #$000F", "STA.w $08A8", "ADC.w #$000B", "STA.w $07A8", "LDA.b $0C", "ADC.w #$0008", "STA.w $08AC", "ADC.w #$0013", "STA.w $07AC")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_83:D82C", "bounds_helper": "CODE_83:D854", "machine_direct_page": "$06A0"},
        "per_tick": {"decrements": ["local $08", "local $0C"], "bounds_helper": "CODE_83:D854"},
        "bounds_writes": {"$08A8": "$08 + $000F", "$07A8": "$08 + $001A", "$08AC": "$0C + $0008", "$07AC": "$0C + $001B"},
        "branches": [
            {"condition": "(actor pointer $00C6 + $000C - $0010) >= local $0C", "effect": "increments local $32 and queues DATA_82:ED71/ED77 through CODE_84:E89C"},
            {"condition": "otherwise", "effect": "calls CODE_84:E894 then updates $07A0/$08A0 from DATA_81:B03D/B031 indexed by local $1A"},
        ],
        "limitations": [
            "The local fields and derived bounds are not named as world axes, hitboxes, or camera coordinates.",
            "The comparison and queue result are not classified as a collision outcome.",
            "DATA_81:B03D/B031 table semantics remain pending despite their observed writes.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
