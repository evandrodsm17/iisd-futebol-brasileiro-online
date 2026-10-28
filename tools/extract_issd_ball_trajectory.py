#!/usr/bin/env python3
"""Recover and validate the ROM-backed ISSD ball trajectory sequencer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TABLE_LABEL = "DATA_83D9A5:"
EXPECTED_TARGETS = ["CODE_83D9B1", "CODE_83D9C7", "CODE_83DA38", "CODE_83DA98", "CODE_83DAD1", "CODE_83DAED"]


def block(lines: list[str], label: str) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    # Local labels (for example CODE_83D9B8) belong to the same handler.
    # Each recovered handler is shorter than this bounded source window.
    return "\n".join(lines[start : start + 120])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    table_start = next(index for index, line in enumerate(lines) if line.strip() == TABLE_LABEL)
    targets = []
    for line in lines[table_start + 1:]:
        line = line.strip()
        if not line.startswith("dw CODE_"):
            break
        targets.append(line.removeprefix("dw "))
    if targets != EXPECTED_TARGETS:
        raise SystemExit(f"unexpected trajectory dispatch table: {targets}")

    checks = {
        "CODE_83D9B1": ("DEC.b $26", "INC.b $2E", "LDA.w #$0010", "STZ.b $16"),
        "CODE_83D9C7": ("CMP.w #$0008", "INC.b $2E", "LDA.w #$0040", "STZ.b $16"),
        "CODE_83DA38": ("LDA.w #$0008", "INC.b $16", "CMP.w #$0005", "STZ.b $26", "INC.b $2E"),
        "CODE_83DA98": ("DEC.b $26", "INC.b $2E", "LDA.w #$0010"),
        "CODE_83DAD1": ("DEC.b $26", "CMP.w #$0008", "INC.b $2E"),
        "CODE_83DAED": ("STA.w $1E6E", "STA.w $1E6C", "TRB.w $11FA"),
    }
    for label, fragments in checks.items():
        body = block(lines, label)
        for fragment in fragments:
            if fragment not in body:
                raise SystemExit(f"{label} no longer contains expected instruction: {fragment}")

    initializer = block(lines, "CODE_83D92D")
    for fragment in ("DATA_81B0BB,y", "DATA_81B0BF,y", "DATA_81B0C3,y", "CPX.w #$0005", "CPX.w #$0007", "ADC.w #$0020", "LDA.w #$5622", "LDA.w #$0040", "STZ.b $2E"):
        if fragment not in initializer:
            raise SystemExit(f"CODE_83D92D no longer contains expected instruction: {fragment}")

    payload = {
        "schema_version": 1,
        "source": {
            "assembly": str(args.asm),
            "dispatcher": "CODE_83:D980 / CODE_83:D99D",
            "dispatch_table": "DATA_83:D9A5",
            "active_blocks": [
                {"direct_page": "08A0", "guard": "WRAM 7E:1E6C is non-negative", "state_offset": "2E"},
                {"direct_page": "08D0", "guard": "WRAM 7E:1E6E is non-negative", "state_offset": "2E"},
            ],
            "initializer": {
                "entry": "CODE_83:D92D",
                "selector_table": "DATA_81:B0BB / DATA_81:B0BF",
                "local_offsets": "DATA_81:B0C3 supplies direct-page $08/$0C; $0C gains $20 for stadium ids 5 and 7",
                "initial_state": "direct-page $22=$5622, $26=$0040, $2E=$0000, and bit $0001 is set in $11FA",
            },
        },
        "states": [
            {"index": 0, "entry": "CODE_83:D9B1", "timer": "decrement 26; on zero set 26=16", "transition": "increment 2E; clear 16"},
            {"index": 1, "entry": "CODE_83:D9C7", "timer": "decrement 26; resource update at 8; on zero set 26=64", "transition": "increment 2E; clear 16"},
            {"index": 2, "entry": "CODE_83:DA38", "timer": "on expiry set 26=8", "transition": "increment 16; after value 5 increment 2E and clear 26"},
            {"index": 3, "entry": "CODE_83:DA98", "timer": "decrement 26; may restore 26=64 from local lookup", "transition": "on zero increment 2E and set 26=16"},
            {"index": 4, "entry": "CODE_83:DAD1", "timer": "decrement 26; resource update at 8", "transition": "on zero increment 2E"},
            {"index": 5, "entry": "CODE_83:DAED", "timer": "no local countdown", "transition": "terminates corresponding block; clears bit 0001 of 11FA only when both blocks ended"},
        ],
        "limitations": [
            "State indexes are ROM control states, not named pass, shot, bounce, net, or post events.",
            "This extractor proves dispatcher structure and local state transitions only; it does not identify the routines that initialize a trajectory block.",
            "The initializer proves local offsets and control fields, not their world-coordinate or velocity semantics.",
            "Collision and browser implementation semantics require additional evidence.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"ball trajectory: OK ({len(targets)} states)")


if __name__ == "__main__":
    main()
