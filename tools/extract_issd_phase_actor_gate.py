#!/usr/bin/env python3
"""Recover the phase-dependent actor eligibility gate in ISSD."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def window(lines: list[str], label: str, length: int = 70) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    return "\n".join(lines[start : start + length])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    body = window(lines, "CODE_83CF7D")
    for fragment in ("LDA.w $00C0", "ASL", "JMP.w (DATA_83CF86,x)", "TDC", "CMP.w $11E8", "LDA.b $30", "CMP.w #$0001", "SEC", "CLC"):
        if fragment not in body:
            raise SystemExit(f"phase actor gate no longer contains: {fragment}")
    start = next(index for index, line in enumerate(lines) if line.strip() == "DATA_83CF86:")
    targets = []
    for line in lines[start + 1:]:
        line = line.strip()
        if not line.startswith("dw CODE_"):
            break
        targets.append(line.removeprefix("dw "))
    if len(targets) != 15 or targets[3] != "CODE_83CFA4" or any(target != "CODE_83CFAA" for index, target in enumerate(targets) if index != 3):
        raise SystemExit(f"unexpected phase gate table: {targets}")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "dispatcher": "CODE_83:CF7D", "table": "DATA_83:CF86", "phase_word": "WRAM 7E:00C0"},
        "entries": {"count": 15, "special_index": 3, "default_target": "CODE_83:CFAA", "special_target": "CODE_83:CFA4"},
        "eligibility": {
            "default": "returns SEC only when current actor local 30 equals 0001; otherwise CLC",
            "index_3": "returns SEC when direct-page accumulator is zero and equals 11E8, or falls through to default local-30 test",
        },
        "limitations": [
            "The 15 phase indexes have no semantic labels from this routine alone.",
            "The meaning of actor local 30 and global 11E8 is not established here.",
            "This is an actor eligibility gate, not a complete phase-transition implementation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("phase actor gate: OK (15 entries, special index 3)")


if __name__ == "__main__":
    main()
