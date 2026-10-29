"""Extract the initialization contract of collision-machine state 0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 82) -> str:
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
    state0 = block(lines, "CODE_83D78F")
    require(state0, "CODE_83:D78F", "LDY.w $00C6", "LDA.w $002A,y", "CMP.w $12B4", "LDX.w #$0030", "LDX.w #$FFD0", "ADC.w $002A,y", "LDA.w $002C,y", "ADC.w #$0100", "JSL.l CODE_80E19B", "STX.b $08", "STY.b $0C", "STZ.w $06D4", "STZ.w $07D4", "STZ.w $08C4", "STZ.w $08F4", "JSR.w CODE_83DC1C", "JSL.l CODE_83DC5D", "CODE_83D7DD:", "LDA.w #$0100", "JML.l CODE_80D6AB", "CODE_83D7F0:", "STZ.w $11E0", "INC.b $32", "LDA.w #$FFFF", "STA.b $24", "STA.b $28", "LDA.w #DATA_82ED5D", "LDY.w #DATA_82ED63", "JSL.l CODE_84E890", "LDX.w #DATA_82C5B6", "JSL.l CODE_84E88C")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_83:D78F", "machine_direct_page": "$06A0", "next_state": "$32 increment"},
        "origin_setup": {
            "actor_pointer": "$00C6",
            "first_word": "actor+$002A is compared with $12B4; add $0030 when negative, otherwise $FFD0",
            "second_word": "actor+$002C + $0100",
            "normalizer": "CODE_80:E19B returns X/Y stored in local $08/$0C",
        },
        "initialization": {
            "cleared_words": ["$7E:06D4", "$7E:07D4", "$7E:08C4", "$7E:08F4", "$7E:11E0"],
            "gates": ["CODE_83:DC1C at direct page $08A0", "CODE_83:DC5D at direct page $06A0"],
            "failure": "either gate carry branches to CODE_80:D6AB with A=$0100",
            "success": "increments local $32, initializes $24/$28 to $FFFF, updates flags in $02 and $07A2, queues DATA_82:ED5D/ED63 and DATA_82:C5B6",
        },
        "limitations": [
            "Actor offsets, $12B4 comparison, and local $08/$0C are not assigned world-coordinate or collision-shape semantics here.",
            "The two gates and CODE_80:D6AB outcome are not named as a particular gameplay event.",
            "Queued tables are not treated as final graphics without matching runtime OAM/VRAM/CGRAM evidence.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
