"""Extract the statically proved handler chain that schedules the get-up table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 32) -> str:
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
    setup = block(lines, "CODE_84B8F1")
    transition = block(lines, "CODE_84B91E")
    completion = block(lines, "CODE_84B947")
    baseline = block(lines, "CODE_84B833")
    require(setup, "CODE_84:B8F1", "LDA.w #$03B8", "JSR.w CODE_84854E", "STZ.b $2E", "LDA.w #$0080", "STA.b $70", "LDY.w #DATA_82E335", "JSR.w CODE_84E65A")
    require(transition, "CODE_84:B91E", "DEC.b $70", "BEQ.b CODE_84B935", "JSR.w CODE_848548", "LDA.w #$0004", "LDA.w #DATA_82DB5B", "JMP.w CODE_84E60C")
    require(completion, "CODE_84:B947", "JSR.w CODE_84E5D1", "BEQ.b CODE_84B94D", "JMP.w CODE_84B833")
    require(baseline, "CODE_84:B833", "LDA.w #$0398", "JSR.w CODE_84854E", "LDA.w #DATA_82D320", "JMP.w CODE_84E60C")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "handler_table": "DATA_81:BD58", "entries": ["CODE_84:B8F1", "CODE_84:B91E", "CODE_84:B947", "CODE_84:B833"]},
        "known_records": [
            {"byte_offset": "$03B8", "handler": "CODE_84:B91E"},
            {"byte_offset": "$03C0", "handler": "CODE_84:B947"},
            {"byte_offset": "$0398", "handler": "CODE_84:B84B"},
        ],
        "proved_flow": [
            {"entry": "CODE_84:B8F1", "effect": "loads handler record $03B8, sets $70 to $0080, and initializes a sequence through CODE_84:E65A"},
            {"entry": "CODE_84:B91E", "condition": "$70 becomes zero", "effect": "CODE_84:8548 advances the current record from $03B8 to $03C0 and dispatches DATA_82:DB5B through CODE_84:E60C"},
            {"entry": "CODE_84:B947", "condition": "CODE_84:E5D1 returns zero", "effect": "jumps to CODE_84:B833, which loads record $0398 and dispatches DATA_82:D320"},
        ],
        "limitations": [
            "The branch that reaches CODE_84:B8F1 is not named as a particular collision, input, or gameplay event.",
            "The return condition from CODE_84:E5D1 is preserved as a machine condition, not a proven animation-complete semantic.",
            "This does not prove final OAM, palette, or complete frame coverage for DB5B or D320.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
