"""Extract the static schedulers entered by ISSD goalkeeper dive modes 1 and 2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def table(lines: list[str], label: str) -> list[str]:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    values = []
    for line in lines[start + 1:]:
        item = line.strip()
        if not item.startswith("dw CODE_"):
            break
        values.append(item.removeprefix("dw "))
    return values


def block(lines: list[str], label: str, count: int = 44) -> str:
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
    mode_one = table(lines, "DATA_A4BE66")
    mode_two = table(lines, "DATA_869BF8")
    if len(mode_one) != 13 or len(mode_two) != 13:
        raise ValueError(f"unexpected scheduler sizes: {len(mode_one)}, {len(mode_two)}")
    require(block(lines, "CODE_A4BE2E"), "CODE_A4:BE2E", "LDA.w #$0001", "STA.w $14A8", "LDA.w #CODE_A4BE46")
    require(block(lines, "CODE_A4BE53"), "CODE_A4:BE53", "LDA.b $22", "ASL", "JMP.w (DATA_A4BE66,x)")
    require(block(lines, "CODE_869BDA"), "CODE_86:9BDA", "LDA.w #$0002", "STA.w $14A8", "LDA.w #CODE_869BE6")
    require(block(lines, "CODE_869BE6"), "CODE_86:9BE6", "JSR.w CODE_86A1DF", "JSR.w CODE_86A659", "JMP.w (DATA_869BF8,x)")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "mode_selector": "$7E:14A8", "mode_dispatch": "DATA_83:DCAA"},
        "schedulers": [
            {
                "mode": 1,
                "entry": "CODE_A4:BE2E",
                "scheduler": "CODE_A4:BE53",
                "state_selector": "$22 shifted left into X",
                "dispatch_table": "DATA_A4:BE66",
                "entries": [{"index": index, "entry": entry} for index, entry in enumerate(mode_one)],
            },
            {
                "mode": 2,
                "entry": "CODE_86:9BDA",
                "scheduler": "CODE_86:9BE6",
                "state_selector": "X prepared by CODE_86:A1DF/CODE_86:A659 before dispatch",
                "dispatch_table": "DATA_86:9BF8",
                "entries": [{"index": index, "entry": entry} for index, entry in enumerate(mode_two)],
            },
        ],
        "limitations": [
            "Scheduler indexes are native control states, not named goalkeeper moves or directions.",
            "The mode-2 X derivation is not decoded beyond its two helper calls.",
            "Visual pose, input, ball state, and transition timing still need runtime correlation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
