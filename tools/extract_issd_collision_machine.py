#!/usr/bin/env python3
"""Recover and validate the ROM-backed ISSD collision control dispatcher."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = ["CODE_83D78F", "CODE_83D82C", "CODE_83D881", "CODE_83D8A8", "CODE_83D8A9", "CODE_83D8E6", "CODE_83D910", "CODE_83D8A8"]


def source_window(lines: list[str], label: str) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    return "\n".join(lines[start : start + 130])


def table_words(lines: list[str], label: str) -> list[str]:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    values: list[str] = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.endswith(":") or not stripped.startswith("dw "):
            break
        values.extend(item.strip() for item in stripped.removeprefix("dw ").split(","))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == "DATA_83D77F:")
    targets = []
    for line in lines[start + 1:]:
        line = line.strip()
        if not line.startswith("dw CODE_"):
            break
        targets.append(line.removeprefix("dw "))
    if targets != EXPECTED:
        raise SystemExit(f"unexpected collision dispatch table: {targets}")

    checks = {
        "CODE_83D78F": ("INC.b $32", "STA.b $24", "STA.b $28"),
        "CODE_83D82C": ("DEC.b $08", "DEC.b $0C", "INC.b $32"),
        "CODE_83D881": ("LDY.b $1A", "CPY.w #$0006", "INC.b $32"),
        "CODE_83D8A8": ("RTL",),
        "CODE_83D8A9": ("LDA.b $36", "CPY.w #$0008", "INC.b $36"),
        "CODE_83D8E6": ("DEC.b $08", "STA.w $0008,y", "STA.w $000C,y"),
        "CODE_83D910": ("JSL.l CODE_83D881", "STA.w $0010,x"),
    }
    for label, fragments in checks.items():
        body = source_window(lines, label)
        for fragment in fragments:
            if fragment not in body:
                raise SystemExit(f"{label} no longer contains expected instruction: {fragment}")

    referenced_tables = {}
    table_counts = {"DATA_81B031": 6, "DATA_81B03D": 5, "DATA_81B047": 5, "DATA_81B051": 6, "DATA_81B05D": 6}
    for label, expected_count in table_counts.items():
        values = table_words(lines, label)
        if len(values) != expected_count:
            raise SystemExit(f"unexpected {label} size: {len(values)}")
        referenced_tables[label] = values

    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "dispatcher": "CODE_83:D774", "dispatch_table": "DATA_83:D77F", "direct_page": "06A0", "state_offset": "32"},
        "states": [
            {"index": 0, "entry": "CODE_83:D78F", "observed": "initializes local bounds and trajectory-related fields; increments 32"},
            {"index": 1, "entry": "CODE_83:D82C", "observed": "decrements local 08/0C, refreshes bounds, may increment 32"},
            {"index": 2, "entry": "CODE_83:D881", "observed": "updates 07A0/08A0 from tables indexed by 1A; at index 6 increments 32 and clears 36"},
            {"index": 3, "entry": "CODE_83:D8A8", "observed": "returns immediately"},
            {"index": 4, "entry": "CODE_83:D8A9", "observed": "table update branch; uses 36 and table index 1A, with an index-8 one-time branch"},
            {"index": 5, "entry": "CODE_83:D8E6", "observed": "decrements local 08/0C, writes adjusted values to actor offsets 08/0C, then branches to state-1 logic"},
            {"index": 6, "entry": "CODE_83:D910", "observed": "runs state-2 logic then writes table value to actor offset 10"},
            {"index": 7, "entry": "CODE_83:D8A8", "observed": "duplicate immediate-return entry"},
        ],
        "referenced_tables": referenced_tables,
        "limitations": [
            "The ROM table establishes control-flow states; it does not name them as wall, player, post, net, pass, or shot collisions.",
            "Tables DATA_81:B031/B03D/B047/B051/B05D and external routines require separate semantic recovery.",
            "No browser physics behavior is derived from this artifact until runtime evidence identifies the state initializers and values.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"collision machine: OK ({len(targets)} states)")


if __name__ == "__main__":
    main()
