"""Extract the ROM offset table shared by actor-context lookup routines."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def block(lines: list[str], label: str, count: int = 24) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + count])


def words(lines: list[str], label: str) -> list[int]:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    values: list[int] = []
    for line in lines[start + 1:]:
        item = line.strip()
        if not item.startswith("dw "):
            break
        values.extend(int(value, 16) for value in re.findall(r"\$([0-9A-Fa-f]{4})", item))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    values = words(lines, "DATA_8195EB")
    expected = list(range(0x3E00, 0x3EC0, 0x000A))
    if values != expected:
        raise ValueError("DATA_81:95EB values changed")
    e8ad = block(lines, "CODE_80E8AD")
    dbdc = block(lines, "CODE_83DBDC")
    for needle in ("AND.w #$001F", "ASL", "ADC.w DATA_8195EB,x", "LDA.l $7E0000,x"):
        if needle not in e8ad:
            raise ValueError(f"CODE_80:E8AD no longer contains {needle}")
    for needle in ("LDA.l $7E0000,x", "AND.w #$001F", "ASL", "LDA.w DATA_8195EB,x", "CMP.w #$08A0", "ADC.w #$00C8", "LDA.l $7E0005,x"):
        if needle not in dbdc:
            raise ValueError(f"CODE_83:DBDC no longer contains {needle}")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "table": "DATA_81:95EB"},
        "words": [f"${value:04X}" for value in values],
        "shape": {"count": len(values), "first": "$3E00", "step": "$000A", "last": "$3EBE"},
        "consumers": [
            {"entry": "CODE_80:E8AD", "use": "adds selected table word and a context bias to saved A before a WRAM word read"},
            {"entry": "CODE_83:DBDC", "use": "uses selected table word as a WRAM base, conditionally adds $00C8, then reads byte +$0005"},
        ],
        "limitations": [
            "Table index values are masked to five bits by the observed consumers, but the semantic slot domain is not named here.",
            "The values are offsets used with runtime WRAM, not ROM player records or browser entity identifiers.",
            "No gameplay or sprite meaning is inferred from either consumer's final read.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
