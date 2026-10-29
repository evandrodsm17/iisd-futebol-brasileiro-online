"""Extract the native eight-step index adjustment adjacent to locomotion gates."""

from __future__ import annotations

import argparse
import json
import re
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


def byte_values(text: str) -> list[str]:
    return re.findall(r"\$[0-9A-F]{2}", text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    routine = block(lines, "CODE_80DD47", 28)
    turn_table = block(lines, "DATA_819629", 3)
    flags_table = block(lines, "DATA_81967A", 5)
    require(routine, "CODE_80:DD47", "TAY", "SBC.b $2E", "AND.w #$0007", "LDA.w DATA_819629,x", "BMI.b CODE_80DD59", "INC", "DEC", "STA.b $2E", "ASL", "ADC.b $5A", "AND.w #$FFBF", "ORA.w DATA_81967A,x", "STA.b $04", "CPY.b $2E", "RTL")
    require(turn_table, "DATA_81:9629", "db $D0,$58,$00,$00,$00,$00,$80,$80,$80")
    turn_bytes = byte_values(turn_table)
    flag_bytes = byte_values(flags_table)
    if len(turn_bytes) != 9 or len(flag_bytes) != 48:
        raise ValueError("turn tables changed shape")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:DD47", "turn_table": "DATA_81:9629", "flag_table": "DATA_81:967A"},
        "index_update": {"difference": "(A - local $2E) & $0007", "choice": "negative byte from DATA_81:9629 decrements local $2E; nonnegative increments it", "normalization": "local $2E &= $0007", "comparison": "returns after comparing original A (in Y) with updated local $2E"},
        "flag_update": {"index": "(local $2E << 1) + local $5A", "destination": "local $04", "operation": "clear bit $0040 then OR DATA_81:967A[index]"},
        "tables": {"DATA_81:9629": turn_bytes, "DATA_81:967A": flag_bytes},
        "limitations": [
            "A and local $2E are native indices; this routine does not prove their human direction labels.",
            "The sign test and bit $0040 update are preserved as control data, not translated into a browser turning rule.",
            "The caller that supplies A must be traced before user input can be associated with this adjustment.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
