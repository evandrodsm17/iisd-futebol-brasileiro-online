"""Extract the low-nibble lookup that feeds shared index adjustment."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def block(lines: list[str], label: str, count: int) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + count])


def require(text: str, label: str, *needles: str) -> None:
    for needle in needles:
        if needle not in text:
            raise ValueError(f"{label} no longer contains {needle}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    helper = block(lines, "CODE_80DE35", 7)
    table = block(lines, "DATA_81963A", 6)
    require(helper, "CODE_80:DE35", "TAY", "CODE_80DE36:", "LDA.w DATA_81963A,y", "AND.w #$000F", "RTL")
    values = re.findall(r"\$[0-9A-F]{2}", table)
    if len(values) != 64:
        raise ValueError("DATA_81:963A changed shape")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "direct_entry": "CODE_80:DE36", "accumulator_entry": "CODE_80:DE35", "table": "DATA_81:963A"},
        "contract": {"direct_entry": "Y indexes DATA_81:963A; A receives the table byte masked with $000F", "accumulator_entry": "copies A to Y, then executes the direct entry"},
        "table_bytes": values,
        "low_nibbles": [f"${int(value[1:], 16) & 0x0F:02X}" for value in values],
        "limitations": [
            "The source index and resulting low nibble are not assigned direction labels by this extraction.",
            "High bits are deliberately retained in table_bytes but ignored by this helper after masking.",
            "This maps native indices only; it does not identify a controller input source.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
