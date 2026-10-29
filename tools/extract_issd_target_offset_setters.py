"""Extract two table-driven setters of the shared target scratch pair."""

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


def words(text: str) -> list[str]:
    return re.findall(r"\$[0-9A-F]{4}", text)


def pairs(values: list[str]) -> list[dict[str, object]]:
    return [{"index": index // 2, "offset_0408": values[index], "offset_040c": values[index + 1]} for index in range(0, len(values), 2)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    first = block(lines, "CODE_80DE3D", 17)
    second = block(lines, "CODE_80DE55", 15)
    table_a = block(lines, "DATA_8197C2", 4)
    table_b = block(lines, "DATA_8197E2", 4)
    require(first, "CODE_80:DE3D", "LDA.b $2E", "CODE_80DE3F:", "ASL", "TAY", "LDA.b $08", "ADC.w DATA_8197C2,y", "STA.w $0408", "LDA.b $0C", "ADC.w DATA_8197C2+$02,y", "STA.w $040C", "RTL")
    require(second, "CODE_80:DE55", "LDA.b $2E", "ASL", "TAY", "ADC.w DATA_8197E2,y", "STA.w $0408", "ADC.w DATA_8197E2+$02,y", "STA.w $040C", "RTL")
    a_values, b_values = words(table_a), words(table_b)
    if len(a_values) != 16 or len(b_values) != 16:
        raise ValueError("target offset table shape changed")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "first_entry": "CODE_80:DE3D / CODE_80:DE3F", "second_entry": "CODE_80:DE55", "index": "local $2E shifted left twice"},
        "common_formula": "target $0408/$040C = local $08/$0C + selected table word pair",
        "tables": {"DATA_81:97C2": pairs(a_values), "DATA_81:97E2": pairs(b_values)},
        "limitations": [
            "The eight index values are not assigned human direction names.",
            "The target pair remains shared scratch; these setters do not identify a permanent target entity.",
            "The offsets are native words and are not translated to browser coordinates.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
