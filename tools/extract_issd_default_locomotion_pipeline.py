#!/usr/bin/env python3
"""Validate the ROM path that assigns default running graphics to a new actor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, length: int) -> str:
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
    entry = block(lines, "CODE_84F80F", 10)
    setup = block(lines, "CODE_84F813", 10)
    state = block(lines, "CODE_84E60C", 125)
    descriptor = block(lines, "CODE_84E6C7", 70)
    running_table = block(lines, "DATA_82CF9F", 7)
    direction_table = block(lines, "DATA_82E34A", 7)
    require(entry, "CODE_84F80F", "JSR.w CODE_84F813", "RTL")
    require(setup, "CODE_84F813", "JSL.l CODE_83F222", "LDA.w #DATA_82CF9F", "LDY.w #DATA_82E34A", "JMP.w CODE_84E60C")
    require(state, "CODE_84E60C", "JSR.w CODE_84E58F", "ADC.w #$0010", "STA.b $18", "LDA.b ($1C),y", "LDA.b ($1A),y")
    require(descriptor, "CODE_84E6C7", "LDA.l DATA_82A3D7&$FF0000,x", "!REGISTER_WriteToVRAMPortLo", "STA.w $0002,y")
    require(running_table, "DATA_82CF9F", "DATA_82CFD7", "DATA_82CFE7", "DATA_82CFC7", "DATA_82CFB7")
    require(direction_table, "DATA_82E34A", "DATA_82E382", "DATA_82E392", "DATA_82E372", "DATA_82E362", "db $04,$03,$03,$03,$04,$03,$03,$03")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "actor_default_entry": "CODE_84:F80F", "default_setup": "CODE_84:F813", "state_setup": "CODE_84:E60C", "descriptor_staging": "CODE_84:E6C7"},
        "default_running": {
            "entry_path": "CODE_84:F80F -> CODE_84:F813 -> CODE_83:F222",
            "script_table": "DATA_82:CF9F",
            "direction_timing_table": "DATA_82:E34A",
            "direction_pointer_pattern": ["E382", "E392", "E3A2", "E392", "E382", "E372", "E362", "E372"],
            "frame_ticks": [4, 3, 3, 3, 4, 3, 3, 3],
            "observed": "the initial actor graphics path assigns the running script and a direction/timing table before selecting descriptor data",
        },
        "descriptor_staging": {
            "entry": "CODE_84:E6C7",
            "descriptor_source": "DATA_82:A3D7 indexed by the selected descriptor pointer",
            "observed": "the routine stages descriptor-derived transfer records and writes the VRAM-port register selector into the record; this artifact does not decode every descriptor field or claim an OAM layout",
        },
        "limitations": [
            "Repeated direction pointers are raw table aliases; their visual symmetry or flip behavior must not be inferred without the complete descriptor and attribute path.",
            "This confirms default running setup only; it does not classify walking, kicks, slides, goalkeeper actions, or gameplay state transitions.",
            "No browser animation behavior changes from this extraction alone."
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("default locomotion pipeline: OK (running script and direction timing table)")


if __name__ == "__main__":
    main()
