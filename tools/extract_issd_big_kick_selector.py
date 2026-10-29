"""Extract the native selection contract for the two strong-kick script tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 24) -> str:
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
    selector = block(lines, "CODE_84B9A0")
    require(
        selector,
        "CODE_84:B9A0",
        "JSR.w CODE_848548",
        "LDA.w #$0008",
        "STA.b $70",
        "LDA.b $6E",
        "AND.w #$0001",
        "ASL\n\tASL",
        "STA.b $2E",
        "JSL.l CODE_80DD82",
        "LDY.w #DATA_82D007",
        "CPX.w #$0005",
        "BCC.b CODE_84B9C0",
        "LDY.w #DATA_82D100",
        "LDA.w #DATA_82D017",
        "JMP.w CODE_84E600",
    )
    payload = {
        "schema_version": 1,
        "source": {
            "assembly": str(args.asm),
            "entry": "CODE_84:B9A0",
            "control_bytes": "DATA_82:D017",
        },
        "selection": {
            "preparation": "CODE_84:8548 is called before selection",
            "local_timer": {"field": "$70", "assigned": "$0008"},
            "orientation_variant": {
                "source": "bit 0 of $6E",
                "destination": "$2E",
                "transform": "mask bit 0 then shift left twice",
                "possible_values": ["$0000", "$0004"],
            },
            "script_table_variant": {
                "index_producer": "CODE_80:DD82",
                "register": "X",
                "comparison": "CPX #$0005",
                "less_than": "DATA_82:D007",
                "greater_or_equal": "DATA_82:D100",
            },
            "dispatcher": "CODE_84:E600",
        },
        "limitations": [
            "This proves static control flow only; it does not map either table to a controller button.",
            "The meaning of CODE_80:DD82 return value X is not decoded here.",
            "It does not prove final OAM, palette, VRAM composition, or every visual pose of either table.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
