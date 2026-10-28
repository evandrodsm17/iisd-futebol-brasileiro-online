#!/usr/bin/env python3
"""Validate the ROM pipeline that activates ISSD trajectory blocks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def window(lines: list[str], label: str, length: int) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    return "\n".join(lines[start : start + length])


def verify(body: str, label: str, *fragments: str) -> None:
    for fragment in fragments:
        if fragment not in body:
            raise SystemExit(f"{label} no longer contains expected instruction: {fragment}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    activate = window(lines, "CODE_869E48", 70)
    load = window(lines, "CODE_86AAB0", 35)
    dispatcher = window(lines, "CODE_83D920", 58)
    verify(activate, "CODE_869E48", "LDA.b $F4", "STA.b $D0", "LDA.b $22", "ASL", "LDA.b $D0", "STA.w $1E6C,x", "JSL.l CODE_869CE5")
    verify(load, "CODE_86AAB0", "LDA.b $22", "ASL", "LDA.w $1E6C,x", "STA.b $F4")
    verify(dispatcher, "CODE_83D920", "LDY.w #$0000", "LDY.w #$0002", "LDA.w DATA_81B0BB,y", "LDA.w DATA_81B0BF,y", "TSB.w $11FA", "STZ.b $2E")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "activation": "CODE_86:9E48", "source_load": "CODE_86:AA91", "trajectory_loader": "CODE_83:D920"},
        "activation_flow": [
            "CODE_86AAB0 reads 1E6C plus (22 << 1) into local F4",
            "CODE_869E48 copies F4 to D0 and stores D0 at 1E6C plus (22 << 1)",
            "the index expression selects word 1E6C or 1E6E for observed 22 values 0 or 1",
            "CODE_83D920 visits both word selectors through DATA_81B0BB and activates direct pages 08A0/08D0 through DATA_81B0BF when the corresponding value is non-negative",
            "the loader sets 11FA bit 0001, initializes local 26 to 0040 and local 2E to zero",
        ],
        "limitations": [
            "The script/interpreter meaning that supplies F4 is unresolved; this does not identify pass, shot, bounce, or net events.",
            "The valid domain and semantics of local 22 require runtime evidence beyond the observed two selector words.",
            "No browser trajectory is replaced until coordinate and velocity sources are recovered.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("trajectory activation: OK")


if __name__ == "__main__":
    main()
