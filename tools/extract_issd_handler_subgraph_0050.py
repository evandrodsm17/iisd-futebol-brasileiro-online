"""Extract the structural handler subgraph rooted at native record $0050."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 64) -> str:
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
    entry = block(lines, "CODE_848A3D", 16)
    primary = block(lines, "CODE_848A51", 54)
    secondary = block(lines, "CODE_848AAF", 68)
    tertiary = block(lines, "CODE_848B15", 38)
    require(entry, "CODE_84:8A3D", "LDA.w #$0050", "JSR.w CODE_84854E", "LDA.w #DATA_82DA56", "LDY.w #DATA_82E3E4^$8000", "JMP.w CODE_84E6AC")
    require(primary, "CODE_84:8A51", "JSL.l CODE_80DD31", "BCS.b CODE_848A83", "JSL.l CODE_80DF67", "JMP.w CODE_84878A", "CODE_848A92:", "LDA.w #DATA_82DA66", "LDY.w #DATA_82E8C4^$8000", "LDA.w #$0058", "JMP.w CODE_84854E")
    require(secondary, "CODE_84:8AAF", "JSL.l CODE_80DD31", "BCC.b CODE_848B0A", "JMP.w CODE_84E619", "JMP.w CODE_84E641", "CODE_848B0A:", "LDA.w #$0060", "JMP.w CODE_84854E")
    require(tertiary, "CODE_84:8B15", "JSL.l CODE_80DD31", "JMP.w CODE_848A92", "JSR.w CODE_84E5D1", "CODE_848B40:", "JMP.w CODE_848A3D")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "handler_table": "DATA_81:BD58", "root": "CODE_84:8A3D"},
        "records": [
            {"byte_offset": "$0050", "handler": "CODE_84:8A51"},
            {"byte_offset": "$0058", "handler": "CODE_84:8AAF"},
            {"byte_offset": "$0060", "handler": "CODE_84:8B15"},
        ],
        "proved_edges": [
            {"from": "CODE_84:8A3D", "to": "$0050", "effect": "dispatches DATA_82:DA56 with DATA_82:E3E4"},
            {"from": "CODE_84:8A51", "to": "$0058", "condition": "its carry path reaches CODE_84:8A92 after the $84 comparison", "effect": "dispatches DATA_82:DA66 with DATA_82:E8C4 and installs $0058"},
            {"from": "CODE_84:8AAF", "to": "$0060", "condition": "CODE_80:DD31 does not carry", "effect": "sets $70 to $0004 and installs $0060"},
            {"from": "CODE_84:8B15", "to": "CODE_84:8A3D", "condition": "its CODE_84:E5D1 path reaches CODE_84:8B40", "effect": "returns to the $0050 setup"},
        ],
        "limitations": [
            "This subgraph is a native control-flow fact, not a label for walking, turning, or any other human-readable action.",
            "Carry values, $84 comparisons, and E5D1 outcomes remain unnamed native conditions.",
            "The sequence tables do not establish final sprite composition or physical effects.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
