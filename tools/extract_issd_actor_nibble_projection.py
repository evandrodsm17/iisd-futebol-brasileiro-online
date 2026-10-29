"""Extract the projection-table consumer of the actor low-nibble field."""

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
    selector = block(lines, "CODE_80E7F8", 40)
    table_a = block(lines, "DATA_819A16", 3)
    table_b = block(lines, "DATA_819A26", 3)
    require(selector, "CODE_80:E7F8", "LDX.w $0088", "LDA.w $0013,x", "AND.w #$000F", "TAY", "LDA.b $6E", "LSR", "BCS.b CODE_80E81A", "CODE_80E807:", "LDA.w $12A2", "ADC.b $42", "STA.w $00AE", "LDA.w DATA_819A26,y", "CODE_80E81A:", "LDA.b $42", "EOR.w #$FFFF", "STA.w $00AE", "LDA.w DATA_819A16,y", "STA.b $40", "LDA.w $12D8", "ADC.b $40", "STA.w $00B0")
    require(table_a, "DATA_81:9A16", "db $00,$01,$00,$00,$28,$21,$14,$14,$D8,$DF,$EC,$EC,$00,$01,$00,$00")
    require(table_b, "DATA_81:9A26", "db $00,$00,$01,$00,$28,$14,$21,$14,$D8,$EC,$DF,$EC,$00,$00,$01,$00")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:E7F8", "actor_pointer": "$0088", "field": "actor+$0013 low nibble"},
        "branch": {"condition": "carry from logical shift right of local $6E", "clear_carry": {"table": "DATA_81:9A26", "base": "$12A2 + local $42", "output": "$00AE"}, "set_carry": {"table": "DATA_81:9A16", "base": "$12D8 - local $42", "output": "$00B0"}},
        "tables": {"DATA_81:9A16": ["$00", "$01", "$00", "$00", "$28", "$21", "$14", "$14", "$D8", "$DF", "$EC", "$EC", "$00", "$01", "$00", "$00"], "DATA_81:9A26": ["$00", "$00", "$01", "$00", "$28", "$14", "$21", "$14", "$D8", "$EC", "$DF", "$EC", "$00", "$00", "$01", "$00"]},
        "limitations": [
            "The low nibble is a table index here, but is not named as direction or animation state.",
            "The output fields $00AE/$00B0 are not promoted to screen coordinates without a full caller/context trace.",
            "The carry source local $6E is a native branch condition, not a confirmed camera-side rule.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
