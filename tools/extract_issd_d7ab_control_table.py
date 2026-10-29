"""Extract the raw control records paired with the D79B native sequence table."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def block(lines: list[str], label: str, count: int = 20) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + count])


def table_bytes(lines: list[str], label: str) -> list[int]:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    values: list[int] = []
    for line in lines[start + 1:]:
        item = line.strip()
        if not item.startswith("db "):
            break
        values.extend(int(value, 16) for value in re.findall(r"\$([0-9A-Fa-f]{2})", item))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    values = table_bytes(lines, "DATA_82D7AB")
    if len(values) != 20:
        raise ValueError(f"unexpected DATA_82:D7AB byte count: {len(values)}")
    selector = block(lines, "CODE_848A1A")
    for needle in ("JSL.l CODE_80E8AD", "AND.w #$00F0", "LSR\n\tLSR\n\tLSR", "AND.w #$001C", "ADC.w #DATA_82D7AB", "LDY.w #DATA_82D79B", "JMP.w CODE_84E600"):
        if needle not in selector:
            raise ValueError(f"CODE_84:8A1A no longer contains {needle}")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "control_table": "DATA_82:D7AB", "sequence_table": "DATA_82:D79B", "selector": "CODE_84:8A1A"},
        "records": [{"index": index, "bytes": [f"${value:02X}" for value in values[index * 4:(index + 1) * 4]]} for index in range(5)],
        "selection": "CODE_84:8A1A masks the high byte of CODE_80:E8AD result, shifts it right three times, masks $001C, and adds it to DATA_82:D7AB before dispatching D79B through CODE_84:E600",
        "limitations": [
            "The four bytes are raw native controls; they are not declared as frame durations, pose counts, or physics values.",
            "The meaning of CODE_80:E8AD and which runtime condition selects each record remains unknown.",
            "D79B composition still requires matching OAM, VRAM, and CGRAM for a final sprite export.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
