#!/usr/bin/env python3
"""Validate the actor-slot selection helpers used by ISSD collision control."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def window(lines: list[str], label: str) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    return "\n".join(lines[start : start + 55])


def verify(body: str, label: str, fragments: tuple[str, ...]) -> None:
    for fragment in fragments:
        if fragment not in body:
            raise SystemExit(f"{label} no longer contains expected instruction: {fragment}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    primary = window(lines, "CODE_83DC1C")
    secondary = window(lines, "CODE_83DC5D")
    verify(primary, "CODE_83DC1C", ("LDY.w #$000B", "ADC.w #$0100", "LDA.w $001E,x", "LDA.w $0030,x", "STX.b $24"))
    verify(secondary, "CODE_83DC5D", ("LDY.w #$000B", "ADC.w #$0100", "CPX.b $3E", "LDA.w $001E,x", "LDA.w $0030,x", "STX.b $34"))
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "helpers": ["CODE_83:DC1C", "CODE_83:DC5D"], "caller": "CODE_83:D78F"},
        "selection": {
            "slot_bases": ["0500", "1000"],
            "slot_stride": "0100",
            "scan_count": 11,
            "common_rejection": ["actor offset 001E is non-zero", "actor offset 0030 is zero"],
            "primary": {"entry": "CODE_83:DC1C", "output_local_offset": "24", "output_flags": "actor offset 0002 low 9 bits OR 0E00"},
            "secondary": {"entry": "CODE_83:DC5D", "output_local_offset": "34", "extra_rejection": "candidate equals local 3E", "output_flags": "actor offset 0002 low 9 bits merged into local 02"},
        },
        "limitations": [
            "Actor slot roles and the meanings of offsets 001E, 0030, 0002, 24, 34, and 3E are not named by this extractor.",
            "The scan proves candidate filtering, not a complete collision or possession rule.",
            "No browser behavior is changed until a runtime trace associates candidates with ball and player events.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("collision target selection: OK (2 helpers, 11 slots)")


if __name__ == "__main__":
    main()
