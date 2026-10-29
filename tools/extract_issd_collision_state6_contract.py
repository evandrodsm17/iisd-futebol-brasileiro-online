"""Extract the terminal table-write contract of collision state 6."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 10) -> str:
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
    state6 = block(lines, "CODE_83D910")
    table = block(lines, "DATA_81B05D")
    require(state6, "CODE_83:D910", "JSL.l CODE_83D881", "CODE_83D914:", "LDY.b $1A", "LDX.w $00C6", "LDA.w DATA_81B05D,y", "STA.w $0010,x", "RTL")
    require(table, "DATA_81:B05D", "dw $0000,$FFF0,$FFF8,$0000,$FFF8,$FFF0")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_83:D910", "shared_write": "CODE_83:D914"},
        "delegation": {"callee": "CODE_83:D881", "contract": "collision state 2 update executes before the shared actor write"},
        "actor_write": {"actor_pointer": "$00C6", "index": "local $1A", "table": "DATA_81:B05D", "destination": "actor+$0010", "table_words": ["$0000", "$FFF0", "$FFF8", "$0000", "$FFF8", "$FFF0"]},
        "limitations": [
            "The actor field at +$0010 is not named as a coordinate, velocity, or collision value.",
            "State 6 has no independent termination branch; the preceding state 2 helper owns its observed transition.",
            "The table words are preserved raw and are not converted to browser units.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
