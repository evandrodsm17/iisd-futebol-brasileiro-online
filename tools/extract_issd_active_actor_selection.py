#!/usr/bin/env python3
"""Validate the ROM routine that refreshes ISSD global actor pointer 11E8."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == "CODE_83C532:")
    body = "\n".join(lines[start : start + 60])
    for fragment in ("LDX.w $11E8", "LDA.w $009A,x", "LDA.w $00FE,y", "LDA.w $00FF,y", "ADC.w $00D4,y", "STA.w $11E8", "LDA.w $0030,x", "JSL.l CODE_83C524", "STA.b $A6"):
        if fragment not in body:
            raise SystemExit(f"CODE_83C532 no longer contains expected instruction: {fragment}")
    helper_start = next(index for index, line in enumerate(lines) if line.strip() == "CODE_83C524:")
    helper = "\n".join(lines[helper_start : helper_start + 20])
    for fragment in ("LDA.w $0030,y", "SBC.w #$0100", "BRA.b CODE_83C524"):
        if fragment not in helper:
            raise SystemExit(f"CODE_83C524 no longer contains expected instruction: {fragment}")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "selector": "CODE_83:C532", "active_slot_helper": "CODE_83:C524", "global_pointer": "WRAM 7E:11E8"},
        "observed_flow": [
            "returns immediately when 11E8 is zero",
            "uses actor offset 009A as an index to read 00FE/00FF and may derive a new slot from 00D4",
            "if resulting actor offset 0030 is zero, chooses base 0F00 or 1A00 based on slot range and decrements by 0100 until 0030 is non-zero",
            "writes final 11E8 value to local A6",
        ],
        "limitations": [
            "This source does not prove that 11E8 is the human-controlled player; it is an active actor pointer used by multiple subsystems.",
            "Table semantics for 009A, 00FE, 00FF, and 00D4 require additional recovery.",
            "No browser player-selection behavior is changed from this evidence alone.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("active actor selection: OK")


if __name__ == "__main__":
    main()
