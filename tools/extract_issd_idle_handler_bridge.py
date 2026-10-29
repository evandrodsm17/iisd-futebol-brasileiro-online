"""Extract the first native handler records reached from the D320 fallback route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 56) -> str:
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
    first = block(lines, "CODE_8487B8", 88)
    second = block(lines, "CODE_848819", 56)
    third = block(lines, "CODE_848859", 64)
    require(first, "CODE_84:87B8", "JSL.l CODE_80DD31", "BCS.b CODE_848801", "JMP.w CODE_848A3D", "LDA.w #DATA_82D320", "LDA.w #$0018", "JMP.w CODE_84854E")
    require(second, "CODE_84:8819", "JSL.l CODE_80DD31", "JMP.w CODE_84878A", "LDA.w #DATA_82CEF8", "LDY.w #DATA_82E34A", "LDA.w #$0020", "JMP.w CODE_84854E")
    require(third, "CODE_84:8859", "JSL.l CODE_80DD31", "STA.b $84", "JMP.w CODE_84878A", "JSL.l CODE_80E444", "JMP.w CODE_848B43", "JMP.w CODE_84E683")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "handler_table": "DATA_81:BD58", "entries": ["CODE_84:87B8", "CODE_84:8819", "CODE_84:8859"]},
        "records": [
            {"byte_offset": "$0010", "handlers": ["CODE_8487B8", "CODE_84BD27", "CODE_84BD27"]},
            {"byte_offset": "$0018", "handlers": ["CODE_848819", "CODE_84BD87", "CODE_84BD87"]},
            {"byte_offset": "$0020", "handlers": ["CODE_848859", "CODE_84BDD4", "CODE_84BDD4"]},
        ],
        "proved_transitions": [
            {"from": "$0010 / CODE_84:87B8", "condition": "CODE_80:DD31 carry path reaches CODE_84:8801 and differs from current $2E", "effect": "dispatches DATA_82:D320 then installs record $0018"},
            {"from": "$0018 / CODE_84:8819", "condition": "its CODE_80:DD31 carry path reaches CODE_84:8838 with actor bit test clear", "effect": "dispatches DATA_82:CEF8 then installs record $0020"},
            {"from": "$0020 / CODE_84:8859", "condition": "CODE_80:DD31 does not carry", "effect": "jumps to common route CODE_84:878A"},
        ],
        "other_exits": ["CODE_84:8A3D", "CODE_84:B07E", "CODE_84:8B43"],
        "limitations": [
            "The carry result of CODE_80:DD31 and actor bit test are not assigned input or movement semantics here.",
            "Records are native program offsets, not names such as idle, walk, or run.",
            "The descriptor tables D320 and CEF8 do not by themselves validate visual composition.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
