#!/usr/bin/env python3
"""Validate actor-record fields that gate ISSD collision target selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def window(lines: list[str], label: str, length: int = 110) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    return "\n".join(lines[start : start + length])


def require(body: str, label: str, *fragments: str) -> None:
    for fragment in fragments:
        if fragment not in body:
            raise SystemExit(f"{label} no longer contains expected instruction: {fragment}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    init = window(lines, "CODE_868000")
    group_a = window(lines, "CODE_86A2D8")
    group_b = window(lines, "CODE_86A30D")
    require(init, "CODE_868000", "TYA", "STA.w $001E,x", "LDA.w #$0910", "STA.w $0030,x")
    require(group_a, "CODE_86A2D8", "LDA.b $22", "STA.w $001E,x", "CMP.w #$0014")
    require(group_b, "CODE_86A30D", "LDA.b $22", "EOR.w #$0001", "STA.w $001E,x", "CMP.w #$000B")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "initialization": "CODE_86:8000 / CODE_86:8036", "group_setup": ["CODE_86:A2D8", "CODE_86:A30D"]},
        "fields": {
            "001E": {"initialization": "receives Y", "group_setup": "receives local 22; second group writes local 22 XOR 0001", "collision_gate": "must be zero for both DC1C and DC5D selectors"},
            "0030": {"initialization": "0910", "collision_gate": "must be non-zero for both DC1C and DC5D selectors"},
            "0002": {"collision_use": "low 9 bits copied into collision-local flags"},
        },
        "limitations": [
            "The source excerpts do not assign public semantic names to actor offsets 001E, 0030, or 0002.",
            "The group setup shows assignment patterns but does not alone prove player, team, availability, or collision-role meanings.",
            "Do not map these fields to browser actor properties until runtime captures connect them to a real match event.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("actor collision fields: OK")


if __name__ == "__main__":
    main()
