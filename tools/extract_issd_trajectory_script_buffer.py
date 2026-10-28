#!/usr/bin/env python3
"""Validate the 20-byte script buffer used by ISSD trajectory transfer."""

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
    copy = block(lines, "CODE_86A4B3", 30)
    populate = block(lines, "CODE_86A4A4", 16)
    sequential = block(lines, "CODE_86A4D1", 25)
    transfer = block(lines, "CODE_86AADB", 55)
    table = block(lines, "DATA_81DC7B", 5)
    verify(copy, "CODE_86A4B3", "LDA.b $22", "ASL", "LDX.w DATA_81DC7B,y", "STA.b [$28],y", "CPY.w #$0014")
    verify(populate, "CODE_86A4A4", "LDX.w #$7E3F90", "LDY.w #$81146E", "LDA.w #$0027", "MVN $81146E>>16,$7E3F90>>16")
    verify(sequential, "CODE_86A4D1", "STA.b [$28],y", "INC", "CPY.w #$0014")
    verify(transfer, "CODE_86AADB", "LDY.b $4A", "CPY.w #$000B", "LDY.b $48", "CPY.w #$000B")
    if "dw $146E,$1482" not in table:
        raise SystemExit("DATA_81DC7B sources changed")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "source_table": "DATA_81:DC7B", "copy_routine": "CODE_86:A4B3", "sequential_initializer": "CODE_86:A4D1", "consumer": "CODE_86:AADB"},
        "buffer": {
            "indirect_pointer": "local 28",
            "length_bytes": 20,
            "work_buffer_source_offsets": ["146E", "1482"],
            "population": "CODE_86:A4A4 copies 40 bytes from 7E:3F90 to 81:146E; source offsets 146E and 1482 are the two 20-byte halves",
            "alternate_initializer": "writes incrementing byte values 00 through 13",
            "consumer_indexes": ["48", "4A"],
            "partition_boundary": 11,
        },
        "limitations": [
            "The ownership and gameplay purpose of the buffer are not named by this routine.",
            "The two source offsets are in the low-address working-memory context of this routine, not ROM assets that can be extracted statically.",
            "The 11 boundary is a control-flow threshold, not a confirmed field-side or team label.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("trajectory script buffer: OK (20 bytes, boundary 11)")


if __name__ == "__main__":
    main()
