"""Extract the table-update and transition contract of collision state 4."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 39) -> str:
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
    state4 = block(lines, "CODE_83D8A9")
    require(state4, "CODE_83:D8A9", "JSL.l CODE_84E8A0", "BEQ.b CODE_83D8D7", "LDY.b $1A", "LDA.w DATA_81B051,y", "STA.w $07A0", "LDA.w DATA_81B047,y", "STA.w $08A0", "LDA.b $36", "CPY.w #$0008", "INC.b $36", "LDA.w #$08A0", "LDX.w #DATA_82C5B6", "JSL.l CODE_84E88C", "CODE_83D8D7:", "INC.b $32", "LDA.w #DATA_82ED5D", "LDY.w #DATA_82ED63", "JSL.l CODE_84E890", "JMP.w CODE_83D845")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_83:D8A9", "machine_direct_page": "$06A0"},
        "nonzero_helper_path": {"helper": "CODE_84:E8A0", "table_writes": {"$07A0": "DATA_81:B051[$1A]", "$08A0": "DATA_81:B047[$1A]"}, "one_time_branch": "when local $36 is zero and $1A is $0008, increment $36 and queue DATA_82:C5B6 at direct page $08A0", "continuation": "CODE_83:D914"},
        "zero_helper_path": {"effect": "increments local $32, queues DATA_82:ED5D/ED63, then enters CODE_83:D845 table update"},
        "limitations": [
            "The result of CODE_84:E8A0 is not assigned a physical or collision meaning.",
            "Local $36 and index $1A=$0008 are native guards, not named one-shot effects.",
            "Table and queue roles remain structural until runtime correlation establishes their visible or physical impact.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
