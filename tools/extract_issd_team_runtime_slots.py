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
    activity_mask = block(lines, "CODE_86CA23", 60)
    trajectory_compare = block(lines, "CODE_83C71D", 110)
    verify(initialize, "CODE_83C6E6", "STA.l $7E3F90,x", "STA.l $7E3FA4,x", "CPX.w #$0014")
    verify(setup, "CODE_83C94F", "!RAM_ISSD_Global_Player1Team", "LDA.w #$3F90", "!RAM_ISSD_Global_Player2Team", "LDA.w #$3FA4", "JSR.w CODE_83C9C5")
    verify(populate, "CODE_83C9C5", "LDA.w #$000B", "LDA.b ($68),y", "AND.w #$001F", "ADC.w #$0020", "ADC.w #$0100", "DEC.w $0010")
    verify(activity_mask, "CODE_86CA23", "SBC.w !RAM_ISSD_Global_NumberOfPlayersOnFieldForP1", "LDX.w #$3F91", "ORA.b #$20", "AND.b #$DF", "SBC.w !RAM_ISSD_Global_NumberOfPlayersOnFieldForP2", "LDX.w #$3FA5")
    verify(trajectory_compare, "CODE_83C71D", "LDX.w #$7ED864", "LDY.w #$7E3F90", "LDX.w #$7ED878", "LDY.w #$7E3FA4", "JSR.w CODE_83C74F", "BIT.b #$20", "CMP.w $0000,y", "STA.b ($04),y")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "array_initializer": "CODE_83:C6E6", "team_setup": "CODE_83:C94F", "actor_population": "CODE_83:C9C5"},
        "runtime_arrays": {"team_1": "WRAM 7E:3F90, initialized with byte sequence 00..13", "team_2": "WRAM 7E:3FA4, initialized with byte sequence 00..13", "entry_count": 20, "population_entries_per_team": 11},
        "actor_population": {"team_1_actor_base": "0500", "team_2_actor_base": "1000", "actor_stride": "0100", "per_actor_read_stride": "0020", "observed": "each iteration reads a runtime-array byte, skips bit 20 entries, uses low 5 bits as an index into the team data path, then advances actor and source positions"},
        "active_player_mask": {
            "entry": "CODE_86:CA23",
            "team_1_range": "7E:3F91..7E:3FA3",
            "team_2_range": "7E:3FA5..7E:3FB7",
            "control_bit": "20",
            "observed": "for each team, entries after the configured active-player count are ORed with bit 20 and remaining entries are ANDed with DF; slot zero of each 20-byte array is not traversed by this routine",
        },
        "trajectory_selection_compare": {
            "entry": "CODE_83:C71D",
            "guard": "runs only when the player-setting value is below 4 and the corresponding trajectory block 1E6C/1E6E is non-negative",
            "team_1": {"current_array": "7E:3F90", "snapshot": "7E:D864", "trajectory_block": "1E6C"},
            "team_2": {"current_array": "7E:3FA4", "snapshot": "7E:D878", "trajectory_block": "1E6E"},
            "comparison": "CODE_83:C74F scans 11 byte positions, excludes current entries with bit 20, compares current against snapshot, and writes byte selection results through the supplied trajectory-block pointer",
        },
        "limitations": [
            "The arrays are runtime state and may be modified after initialization; this does not freeze a final formation or lineup.",
            "The low-five-bit index, bit-20 activity mask, and trajectory comparison are structural observations, not player-number, control, pass, or shot semantics.",
            "The byte offsets written by CODE_83:C74F have not been given gameplay labels; this extraction does not identify a trajectory as a pass or shot.",
            "No web roster movement or actor spawning behavior is changed from this extraction alone.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("team runtime slots: OK (20 entries, 11 populated actors per team)")


if __name__ == "__main__":
    main()
