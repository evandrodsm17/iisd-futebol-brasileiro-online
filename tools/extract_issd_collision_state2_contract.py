"""Extract the update and terminal transition contract of collision state 2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 34) -> str:
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
    state2 = block(lines, "CODE_83D881")
    require(state2, "CODE_83:D881", "JSL.l CODE_84E8A0", "LDY.b $1A", "LDA.w DATA_81B051,y", "STA.w $07A0", "LDA.w DATA_81B047,y", "STA.w $08A0", "CPY.w #$0006", "BEQ.b CODE_83D899", "CODE_83D899:", "INC.b $32", "STZ.b $36", "LDA.w #$08A0", "TCD", "LDX.w #DATA_82C5BB", "JSL.l CODE_84E88C")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_83:D881", "machine_direct_page": "$06A0"},
        "per_tick": {"helper": "CODE_84:E8A0", "index": "local $1A", "table_writes": {"$07A0": "DATA_81:B051[index]", "$08A0": "DATA_81:B047[index]"}},
        "terminal_transition": {"condition": "local $1A equals $0006", "effect": "increments local $32, clears local $36, switches direct page to $08A0, and queues DATA_82:C5BB through CODE_84:E88C"},
        "limitations": [
            "The helper progression and table values are not assigned collision, trajectory, or world-coordinate semantics.",
            "Index value six is a native control-flow threshold, not a named animation or physical phase.",
            "The queued table is not final visual evidence without matching runtime graphics state.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
