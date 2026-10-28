#!/usr/bin/env python3
"""Recover the unlabeled 10-byte player-record reads used to populate actors."""

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
    populate = block(lines, "CODE_83C9C5", 110)
    stride = block(lines, "CODE_83CA79", 20)
    adjustment = block(lines, "CODE_83CA8F", 32)
    require(populate, "CODE_83C9C5", "LDA.w #$000B", "LDA.w $0007,x", "BIT.b #$88", "LDA.w $0000,x", "LDA.w $0002,x", "LDA.w $0004,x", "LDA.w $0005,x", "LDA.w $0006,x", "ADC.w #$0020", "ADC.w #$0100")
    require(stride, "CODE_83CA79", "ADC.w #$000A", "ADC.w $0006", "TAX")
    require(adjustment, "CODE_83CA8F", "LDA.w $0008,x", "ASL", "SBC.b #$04", "ADC.b $62", "SBC.b $40")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "population_entry": "CODE_83:C9C5", "record_addressing": "CODE_83:CA79", "record_adjustment": "CODE_83:CA8F"},
        "record": {"size_bytes": 10, "indexing": "runtime-array low five bits select record_index; CODE_83:CA79 computes team_record_base + record_index * 10", "population_count": 11, "actor_stride": "0100", "source_advance_per_actor": "0020"},
        "observed_reads": [
            {"offset": "00", "operation": "low nibble -> actor +62; high nibble is transformed to 9 - high_nibble -> actor +66"},
            {"offset": "02", "operation": "high nibble -> actor +67"},
            {"offset": "04", "operation": "high nibble -> actor +30"},
            {"offset": "05", "operation": "word is shifted left and stored at actor +56; the team-context word is stored at actor +57"},
            {"offset": "06", "operation": "high nibble is shifted and combined with actor direct-page high byte before storing at actor +03"},
            {"offset": "07", "operation": "bits 80 or 08 skip record-specific population"},
            {"offset": "08", "operation": "CODE_83:CA8F applies a bounded adjustment to actor +62/+66 when (record[8] * 2 - 4) is negative"}
        ],
        "limitations": [
            "Offsets are structural reads and writes, not labels for appearance, speed, position, skill, or player identity.",
            "The source advances by 20 bytes while record lookup is 10 bytes; this extraction does not infer why both strides coexist.",
            "No browser roster, attribute, graphics, or physics value is changed from this artifact alone."
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("runtime player record: OK (10-byte lookup, 11 actor populations)")


if __name__ == "__main__":
    main()
