"""Extract the target-vector to native angular-index transform."""

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


def values(text: str) -> list[str]:
    return re.findall(r"\$[0-9A-F]{2}", text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    routine = block(lines, "CODE_80F46D", 90)
    quadrant = block(lines, "DATA_819B3B", 3)
    slope = block(lines, "DATA_819B3F", 6)
    require(routine, "CODE_80:F46D", "LDA.w $0408", "LDA.w $040C", "LDA.b $08", "LDA.b $0C", "SBC.b $44", "SBC.b $46", "CMP.w #$0008", "LDA.w DATA_819B3F,x", "ADC.w DATA_819B3B,x", "AND.b #$3F", "STA.b $40", "RTL")
    quadrant_values = values(quadrant)
    slope_values = values(slope)
    if quadrant_values != ["$00", "$10", "$30", "$20"] or len(slope_values) != 64:
        raise ValueError("angle tables changed shape")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:F46D", "quadrant_table": "DATA_81:9B3B", "slope_table": "DATA_81:9B3F"},
        "inputs": {"target": ["global $0408", "global $040C"], "origin": ["local $08", "local $0C"]},
        "transform": ["subtract origin from target", "preserve sign/quadrant in local $46 and take absolute magnitudes", "repeatedly divide the larger magnitude and the paired smaller magnitude by four until the larger is below $0008", "form a six-bit lookup index from normalized magnitudes", "lookup DATA_81:9B3F, mirror when required by quadrant bits, add DATA_81:9B3B[quadrant], mask $003F, return in local $40"],
        "tables": {"DATA_81:9B3B": quadrant_values, "DATA_81:9B3F": slope_values},
        "limitations": [
            "The output is a native six-bit angular index, not an asserted screen-space angle unit for browser code.",
            "The roles of target/global and origin/local coordinates require caller-level semantic correlation.",
            "This routine is not a direct user-input decoder.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
