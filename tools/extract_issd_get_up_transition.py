"""Extract the native countdown-to-get-up transition without naming its trigger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 28) -> str:
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
    handler = block(lines, "CODE_84B91E")
    require(handler, "CODE_84:B91E", "DEC.b $70", "BEQ.b CODE_84B935", "DEC.b $72", "BNE.b CODE_84B932", "LDA.w $0078", "AND.w #$0003", "ADC.w #$0003", "BRA.b CODE_84B912", "JMP.w CODE_84E683", "JSR.w CODE_848548", "LDA.w #$0004", "STA.b $2E", "JSL.l CODE_80DD80", "LDA.w #DATA_82DB5B", "JMP.w CODE_84E60C")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_84:B91E", "transition": "CODE_84:B935"},
        "countdown": {
            "primary": {"field": "$70", "operation": "decrement each handler invocation", "zero_branch": "CODE_84:B935"},
            "secondary": {"field": "$72", "operation": "decrement while primary is nonzero", "on_zero": "derive a replacement value from ($0078 & $0003) + $0003 via CODE_84:B912"},
            "nonzero_secondary_path": "CODE_84:E683",
        },
        "transition": {"preparation": "CODE_84:8548", "orientation_destination": {"field": "$2E", "assigned": "$0004"}, "helper": "CODE_80:DD80", "script": "DATA_82:DB5B", "dispatcher": "CODE_84:E60C"},
        "limitations": ["The caller/state that enters CODE_84:B91E is not decoded as a named gameplay event.", "The semantics of $0078 and CODE_84:E683 are not claimed beyond their observed control flow.", "This does not prove controller input, OAM composition, palette, or complete visual timing for DATA_82:DB5B."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
