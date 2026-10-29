"""Extract shared collision-machine routes used by multiple state entries."""

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
    table_update = block(lines, "CODE_83D841", 10)
    advance = block(lines, "CODE_83D873", 26)
    require(table_update, "CODE_83:D841", "JSL.l CODE_84E894", "CODE_83D845:", "LDY.b $1A", "LDA.w DATA_81B03D,y", "STA.w $07A0", "LDA.w DATA_81B031,y", "STA.w $08A0", "RTL")
    require(advance, "CODE_83:D873", "INC.b $32", "LDA.w #DATA_82ED71", "LDY.w #DATA_82ED77", "JSL.l CODE_84E89C", "BRA.b CODE_83D885", "CODE_83D885:", "LDA.w DATA_81B051,y", "STA.w $07A0", "LDA.w DATA_81B047,y", "STA.w $08A0", "CPY.w #$0006", "BEQ.b CODE_83D899", "INC.b $32", "STZ.b $36", "LDX.w #DATA_82C5BB", "JSL.l CODE_84E88C")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "table_update": "CODE_83:D841", "advance": "CODE_83:D873", "shared_tail": "CODE_83:D885"},
        "table_update_route": {"helper": "CODE_84:E894", "writes": {"$07A0": "DATA_81:B03D[$1A]", "$08A0": "DATA_81:B031[$1A]"}},
        "advance_route": {"state_counter": "increments local $32", "queue": {"first": "DATA_82:ED71", "second": "DATA_82:ED77", "routine": "CODE_84:E89C"}, "tail_writes": {"$07A0": "DATA_81:B051[$1A]", "$08A0": "DATA_81:B047[$1A]"}, "terminal_guard": {"condition": "local $1A equals $0006", "effect": "increments local $32, clears local $36, queues DATA_82:C5BB at direct page $08A0"}},
        "limitations": [
            "The helper routines and queued data are not assigned visual, physical, or football semantics.",
            "Local $32, $36, $07A0, and $08A0 retain their raw native roles only.",
            "Call-site-specific conditions are documented by the state contracts, not inferred here.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
