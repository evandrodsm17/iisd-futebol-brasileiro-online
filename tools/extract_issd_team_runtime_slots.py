#!/usr/bin/env python3
"""Validate ISSD runtime team-slot arrays and actor population loop."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, length: int) -> str:
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
    initialize = block(lines, "CODE_83C6E6", 28)
    setup = block(lines, "CODE_83C94F", 80)
    populate = block(lines, "CODE_83C9C5", 115)
    verify(initialize, "CODE_83C6E6", "STA.l $7E3F90,x", "STA.l $7E3FA4,x", "CPX.w #$0014")
    verify(setup, "CODE_83C94F", "!RAM_ISSD_Global_Player1Team", "LDA.w #$3F90", "!RAM_ISSD_Global_Player2Team", "LDA.w #$3FA4", "JSR.w CODE_83C9C5")
    verify(populate, "CODE_83C9C5", "LDA.w #$000B", "LDA.b ($68),y", "AND.w #$001F", "ADC.w #$0020", "ADC.w #$0100", "DEC.w $0010")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "array_initializer": "CODE_83:C6E6", "team_setup": "CODE_83:C94F", "actor_population": "CODE_83:C9C5"},
        "runtime_arrays": {"team_1": "WRAM 7E:3F90, initialized with byte sequence 00..13", "team_2": "WRAM 7E:3FA4, initialized with byte sequence 00..13", "entry_count": 20, "population_entries_per_team": 11},
        "actor_population": {"team_1_actor_base": "0500", "team_2_actor_base": "1000", "actor_stride": "0100", "per_actor_read_stride": "0020", "observed": "each iteration reads a runtime-array byte, skips bit 20 entries, uses low 5 bits as an index into the team data path, then advances actor and source positions"},
        "limitations": [
            "The arrays are runtime state and may be modified after initialization; this does not freeze a final formation or lineup.",
            "The low-five-bit index and bit-20 behavior are structural observations, not player-number or event semantics.",
            "No web roster movement or actor spawning behavior is changed from this extraction alone.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("team runtime slots: OK (20 entries, 11 populated actors per team)")


if __name__ == "__main__":
    main()
