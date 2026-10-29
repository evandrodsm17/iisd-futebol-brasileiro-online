"""Extract the native WRAM lookup contract used by CODE_80:E8AD."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 32) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + count])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    body = block(lines, "CODE_80E8AD")
    for needle in ("STA.b $40", "LDX.w #$3F90", "LDY.w #$0000", "TDC", "CMP.w #$1000", "LDX.w #$3FA4", "LDY.w #$00C8", "ADC.b $68", "LDA.l $7E0000,x", "AND.w #$001F", "ASL", "ADC.w DATA_8195EB,x", "ADC.b $40", "LDA.l $7E0000,x", "RTL"):
        if needle not in body:
            raise ValueError(f"CODE_80:E8AD no longer contains {needle}")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:E8AD", "rom_offset_table": "DATA_81:95EB"},
        "lookup": {
            "input": "A is saved to direct-page $40",
            "context_partition": "direct page below $1000 selects base $3F90 and bias $0000; otherwise base $3FA4 and bias $00C8",
            "first_index": "base + direct-page $68; low 5 bits of the resulting WRAM word are doubled for DATA_81:95EB",
            "second_index": "context bias + DATA_81:95EB word + saved A",
            "return": "word read from WRAM $7E:0000 at second index",
        },
        "limitations": [
            "The direct-page partition, $68, DATA_81:95EB values, and returned word have no human-readable player/control semantics assigned here.",
            "This proves a lookup mechanism, not that every caller uses the returned word as an animation selector.",
            "WRAM content is runtime data and is not distributed by this artifact.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
