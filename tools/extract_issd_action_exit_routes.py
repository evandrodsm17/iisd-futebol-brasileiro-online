"""Extract common native exits reached by player action handlers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 48) -> str:
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
    exit_a = block(lines, "CODE_84878A")
    exit_b = block(lines, "CODE_848DD1")
    require(exit_a, "CODE_84:878A", "JSR.w CODE_84B9D7", "JSL.l CODE_80DF67", "JMP.w CODE_848A3D", "LDA.w #DATA_82D320", "LDY.w #DATA_82E404^$8000", "LDA.w #$0010", "JMP.w CODE_84854E")
    require(exit_b, "CODE_84:8DD1", "JSR.w CODE_84B9D7", "CMP.w $00A6", "LDA.w $00D0", "JMP.w CODE_84878A", "JSL.l CODE_8387C8", "LDA.w #$00B8", "LDA.w #DATA_82D320", "JMP.w CODE_84E60C")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entries": ["CODE_84:878A", "CODE_84:8DD1"], "handler_table": "DATA_81:BD58"},
        "routes": [
            {"entry": "CODE_84:878A", "common_helper": "CODE_84:B9D7", "branch_helper": "CODE_80:DF67", "alternate_target": "CODE_84:8A3D", "fallback": {"script": "DATA_82:D320", "record": "$0010"}},
            {"entry": "CODE_84:8DD1", "common_helper": "CODE_84:B9D7", "guard_words": ["$00A6", "$00D0"], "one_branch": "CODE_84:878A", "other_branch": {"helper": "CODE_83:87C8", "script": "DATA_82:D320", "record": "$00B8"}},
        ],
        "known_records": [
            {"byte_offset": "$0010", "handlers": ["CODE_8487B8", "CODE_84BD27", "CODE_84BD27"]},
            {"byte_offset": "$00B8", "handlers": ["CODE_848E1C", "CODE_84C13F", "CODE_84C26A"]},
        ],
        "limitations": [
            "These are common machine routes; they are not named as generic player control or a guaranteed action completion state.",
            "The return semantics of CODE_80:DF67, CODE_84:B9D7, and guard words $00A6/$00D0 are not decoded here.",
            "D320 table selection alone does not prove a final rendered idle pose without matching OAM, VRAM, and CGRAM.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
