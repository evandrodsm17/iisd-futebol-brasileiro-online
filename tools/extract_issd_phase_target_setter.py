"""Extract the phase/sign-driven target-pair setter at CODE_80:DE6D."""

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


def pairs(values: list[str]) -> list[dict[str, object]]:
    return [{"index": index // 2, "offset_0408": values[index], "offset_040c": values[index + 1]} for index in range(0, len(values), 2)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    routine = block(lines, "CODE_80DE6D", 35)
    table = block(lines, "DATA_819802", 6)
    require(routine, "CODE_80:DE6D", "LDA.b $76", "ADC.b $78", "STA.b $76", "AND.w #$001F", "CMP.w #$0010", "ROR.b $40", "AND.w #$000F", "LDA.w DATA_819802,y", "BPL.b CODE_80DE8D", "EOR.w #$FFFF", "ADC.b $08", "STA.w $0408", "ADC.b $0C", "STA.w $040C", "RTL")
    values = re.findall(r"\$[0-9A-F]{4}", table)
    if len(values) != 32:
        raise ValueError("phase target offset table changed shape")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "entry": "CODE_80:DE6D", "table": "DATA_81:9802"},
        "phase_update": "local $76 = local $76 + local $78; its low five bits are compared to $0010 and the carry is rotated into local $40",
        "selection": "low four bits of updated local $76 select one of sixteen word pairs",
        "sign_handling": "when local $40 is negative, both selected offsets are two's-complement negated before addition",
        "output": "target $0408/$040C = local $08/$0C + selected signed pair",
        "table_pairs": pairs(values),
        "limitations": [
            "Local $76, $78, and $40 are preserved as native state; no phase, direction, or motion label is assigned.",
            "The target pair remains shared scratch and does not establish a fixed target entity.",
            "The signed word offsets are not converted to browser-space units.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
