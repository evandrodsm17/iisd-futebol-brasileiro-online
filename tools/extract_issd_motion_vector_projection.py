"""Extract the table/PPU-multiply motion-vector projection at 80:DDBE."""

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
    routine = block(lines, "CODE_80DDBE", 62)
    selector = block(lines, "DATA_819632", 3)
    require(routine, "CODE_80:DDBE/DDC0", "LDX.b $2E", "CODE_80DDC0:", "LDA.w DATA_819632,x", "STA.b $58", "STZ.b $22", "STZ.b $24", "STZ.b $26", "STZ.b $28", "AND.w #$001F", "ASL", "TAX", "LDA.w DATA_819742,x", "REGISTER_Mode7MatrixParameterA", "REGISTER_Mode7MatrixParameterB", "REGISTER_PPUMultiplicationProductMid", "SBC.w #$0010", "CMP.w #$0020", "STA.b $23", "STA.b $27", "DEC.b $24", "DEC.b $28", "RTL")
    require(selector, "DATA_81:9632", "db $00,$04,$08,$18,$20,$24,$28,$38")
    selector_values = re.findall(r"\$[0-9A-F]{2}", selector)
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "indexed_entry": "CODE_80:DDBE", "direct_entry": "CODE_80:DDC0", "selector_table": "DATA_81:9632", "coefficient_table": "DATA_81:9742"},
        "entry": {"indexed": "X = local $2E, then use DATA_81:9632[X]", "direct": "CODE_80:DDC0 reads DATA_81:9632[X] and masks $00FF", "raw": "CODE_80:DDC6 uses A directly as the selected native value"},
        "initialization": "stores selected value in local $58 and clears local $22/$24/$26/$28",
        "projection": {"coefficient_index": "(local $58 & $001F) << 2", "coefficient_rows": "DATA_81:9742[index] and DATA_81:9742[index + 2]", "scale_input": "low byte of Y is written twice to the Mode 7 matrix-B register for each nonzero coefficient", "outputs": "16-bit stores at $23 and $27 overlap the words at $24 and $28; negation uses two's complement, with DEC at $24/$28 before the overlapping store", "first_axis_negation": "nonzero product and (($58 - $0010) & $FFFF) < $0020", "second_axis_negation": "nonzero product and $58 >= $0020"},
        "selector_bytes": selector_values,
        "limitations": [
            "The local pairs are not named velocity, displacement, or screen coordinates without caller/runtime validation.",
            "Mode 7 multiplication proves arithmetic construction, not a browser-unit scale.",
            "The eight selector values are raw native control values and are not assigned human direction labels.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
