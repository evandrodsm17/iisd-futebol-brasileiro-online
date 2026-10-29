"""Extract the carry/value gate shared by native locomotion handlers."""

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
    gate = block(lines, "CODE_80DD31", 16)
    table = block(lines, "DATA_819613", 4)
    require(gate, "CODE_80:DD31", "LDX.w $0088", "LDA.w $0013,x", "AND.w #$000F", "BEQ.b CODE_80DD45", "TAY", "LDA.w DATA_819613,y", "AND.w #$00FF", "SEC", "RTL", "CODE_80DD45:", "CLC", "RTL")
    require(table, "DATA_81:9613", "db $00,$00,$04,$00,$02,$01,$03,$02,$06,$07,$05,$06,$00,$00,$04,$00")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:DD31", "actor_pointer": "$0088", "field": "actor+$0013 low nibble", "table": "DATA_81:9613"},
        "gate": {"zero_nibble": {"carry": "clear", "accumulator": "not written by this branch"}, "nonzero_nibble": {"carry": "set", "accumulator": "zero-extended DATA_81:9613[nibble]"}},
        "table_bytes": ["$00", "$00", "$04", "$00", "$02", "$01", "$03", "$02", "$06", "$07", "$05", "$06", "$00", "$00", "$04", "$00"],
        "limitations": [
            "The actor pointer, field +$0013, and nibble values are not named as input, direction, or movement state.",
            "Carry callers use the gate structurally; the table result is not converted to a browser movement value.",
            "This does not establish the speed, acceleration, or action identity of a player.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
