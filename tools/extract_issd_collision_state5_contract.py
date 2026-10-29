"""Extract collision state 5 local-to-actor update and branch contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 31) -> str:
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
    state5 = block(lines, "CODE_83D8E6")
    require(state5, "CODE_83:D8E6", "DEC.b $08", "DEC.b $0C", "JSR.w CODE_83D854", "LDY.w $00C6", "LDA.b $08", "ADC.w #$0008", "STA.w $0008,y", "LDA.b $0C", "ADC.w #$000C", "STA.w $000C,y", "LDA.w $002C,y", "CMP.w #$FFF0", "BMI.b CODE_83D90D", "JMP.w CODE_83D841", "CODE_83D90D:", "JMP.w CODE_83D873")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_83:D8E6", "shared_bounds_helper": "CODE_83:D854"},
        "updates": {"decrements": ["local $08", "local $0C"], "actor_pointer": "$00C6", "actor+$0008": "local $08 + $0008", "actor+$000C": "local $0C + $000C"},
        "branches": [
            {"condition": "actor+$002C is below signed $FFF0", "target": "CODE_83:D873 (state-advance path)"},
            {"condition": "otherwise", "target": "CODE_83:D841 (shared table-update path)"},
        ],
        "limitations": [
            "The actor/local fields are not named as spatial coordinates or collision dimensions.",
            "The signed threshold $FFF0 is a branch constant, not a confirmed physical threshold in browser units.",
            "Shared targets retain the limitations documented for state 1.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
