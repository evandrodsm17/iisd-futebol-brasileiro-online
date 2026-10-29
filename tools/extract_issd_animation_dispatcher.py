"""Extract the control-flow contract of the native player animation dispatcher."""

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
    e600 = block(lines, "CODE_84E600", 30)
    e641 = block(lines, "CODE_84E641", 92)
    e6c7 = block(lines, "CODE_84E6C7", 20)
    require(e600, "CODE_84:E600", "STZ.b $1A", "STY.b $1C", "STA.b $18", "JSR.w CODE_84E58F", "ADC.w #$0010", "STA.b $18")
    require(e641, "CODE_84:E641", "DEC.b $16", "LDA.b ($18),y", "STA.b $16", "LDA.b $2E", "LDA.b ($1C),y", "LDA.b ($1A),y", "BRA.b CODE_84E6C7")
    require(e6c7, "CODE_84:E6C7", "STX.b $14", "LDA.w $11E0", "LDA.l DATA_82A3D7&$FF0000,x")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_84:E600", "final_queue": "CODE_84:E6C7"},
        "entry_paths": {
            "CODE_84:E600": {"writes": {"$1A": "$0000", "$1C": "Y", "$18": "A"}, "next": "CODE_84:E645"},
            "CODE_84:E60C": {"writes": {"$1A": "$0000", "$18": "CODE_84:E58F result + $0010"}, "next": "CODE_84:E645"},
            "CODE_84:E641": {"timer": "decrement $16; return when nonzero; otherwise select next item"},
            "CODE_84:E683": {"timer": "decrement $16; return when nonzero; otherwise reuse $18 selection"},
        },
        "selection": {
            "direction_index": "$2E shifted left selects a word from the table pointed by $1C",
            "cursor": "$1A selects a word from the resulting sequence",
            "duration": "low byte of selected control word is written to $16",
            "descriptor": "selected word is normalized and passed in X to CODE_84:E6C7",
            "sign_path": "negative selected word increments $1A by two before queueing; nonnegative clears $1A",
        },
        "queue_boundary": {"descriptor_register": "X copied to $14", "asset_table": "DATA_82:A3D7", "capacity_gate": "$11E0 compared with $11E2"},
        "limitations": [
            "A, Y, $1A, $1C, and $2E are native control values; this artifact does not name them as a particular player action.",
            "The meaning of CODE_84:E58F and the high bits of sequence words is not fully decoded.",
            "Queueing a descriptor does not by itself prove its final OAM, CGRAM palette, or pixels without a matching runtime frame.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
