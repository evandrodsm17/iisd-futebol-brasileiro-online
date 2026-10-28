"""Extract the static directional boundary predicate used by ISSD offside checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int) -> str:
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
    predicate = block(lines, "CODE_80D627", 49)
    require(predicate, "CODE_80:D627", "LDX.b $88", "LDA.w $00C6,x", "LDA.b $6E", "LSR", "BCS.b CODE_80D659")
    require(predicate, "forward branch", "LDA.w #$000C", "LDA.w #$0018", "ADC.b $40", "CMP.w $002A,y", "BMI.b CODE_80D67E")
    require(predicate, "reverse branch", "SBC.b $40", "CMP.w $002A,y", "BMI.b CODE_80D657")
    payload = {
        "schema_version": 1,
        "source": {
            "assembly": str(args.asm),
            "entry": "CODE_80:D627",
            "call_gate": "CODE_80:D5DF",
        },
        "inputs": {
            "candidate_selector": "$88 indexes $00C6 to select an actor context",
            "candidate_axis": "$002A,x after $00C6[$88]",
            "target_axis": "$002A,y; Y is supplied by each caller",
            "direction_bit": "bit 0 of $6E selects one of two mirrored comparisons",
            "bounds": ["$12F2", "$042A"],
        },
        "branches": [
            {
                "when": "bit 0 of $6E is clear",
                "bound_choice": "selects the greater of candidate axis and $12F2; replaces it with $042A when that selected value is below $042A",
                "margin": {"normal": "$000C", "after $042A replacement": "$0018"},
                "comparison": "adds margin, compares with target axis, returns carry set only when the adjusted value is below target",
            },
            {
                "when": "bit 0 of $6E is set",
                "bound_choice": "selects the lesser of candidate axis and $12F2; replaces it with $042A when that selected value is above $042A",
                "margin": {"normal": "$000C", "after $042A replacement": "$0018"},
                "comparison": "subtracts margin, compares with target axis, returns carry set unless the adjusted value is below target",
            },
        ],
        "caller_contract": {
            "gate": "CODE_80:D5DF bypasses this predicate when CurrentOffSideSetting is non-zero; its caller must provide Y",
            "observable_result": "carry is the only stable result exported by CODE_80:D627; D5DF branches on it before writing $00C4",
        },
        "limitations": [
            "The semantic identity of $002A, $12F2, $042A, $88, and the caller-provided Y actor is not asserted by this extraction.",
            "Carry is a directional boundary result, not by itself proof of an offside infraction or its restart.",
            "The browser implementation must wait for runtime correlation before using this predicate as final rule logic.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
