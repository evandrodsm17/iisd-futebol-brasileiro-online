"""Extract static branches from the native handler installed with running graphics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 64) -> str:
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
    running = block(lines, "CODE_848914", 90)
    follow_up = block(lines, "CODE_8489B8", 58)
    alternate = block(lines, "CODE_848A07", 40)
    require(running, "CODE_84:8914", "JSL.l CODE_80F1E3", "JSL.l CODE_80DD31", "BCC.b CODE_848995", "JSL.l CODE_80E49B", "JMP.w CODE_8489F8", "CODE_848995:", "LDA.w #DATA_82CEF8", "LDY.w #DATA_82E34A", "LDA.w #$0010", "STA.b $72", "LDA.w #$0040", "JMP.w CODE_84854E")
    require(alternate, "CODE_84:8A07", "LDA.w #$0048", "ADC.w #DATA_82D7AB", "LDY.w #DATA_82D79B", "JMP.w CODE_84E600")
    require(follow_up, "CODE_84:89B8", "DEC.b $72", "BEQ.b CODE_8489EC", "CODE_8489EC:", "JSL.l CODE_80DD31", "JMP.w CODE_84884C", "JMP.w CODE_84878A")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "handler_table": "DATA_81:BD58", "entries": ["CODE_84:8914", "CODE_84:89B8"]},
        "records": [
            {"byte_offset": "$0038", "handler": "CODE_84:8914"},
            {"byte_offset": "$0040", "handler": "CODE_84:89B8"},
            {"byte_offset": "$0048", "handler": "CODE_84:8A34"},
        ],
        "proved_branches": [
            {"entry": "CODE_84:8914", "condition": "CODE_80:DD31 does not carry, or the subsequent actor bit test is clear", "effect": "dispatches DATA_82:CEF8 with DATA_82:E34A, sets $72 to $0010, and installs record $0040"},
            {"entry": "CODE_84:8914", "condition": "the CODE_80:E49B carry path reaches CODE_84:8A07", "effect": "installs record $0048 and dispatches DATA_82:D7AB with DATA_82:D79B"},
            {"entry": "CODE_84:89B8", "condition": "$72 reaches zero", "effect": "CODE_80:DD31 branches to CODE_84:884C on carry or CODE_84:878A otherwise"},
        ],
        "limitations": [
            "Helper carry results and actor-bit tests are not mapped to keyboard/controller input or named movement intent.",
            "D7AB/D79B are preserved as native tables; this artifact does not promote them to a visual animation label.",
            "No OAM, CGRAM, or physics outcome is inferred from these handler branches.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
