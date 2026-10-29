"""Extract the statically provable handler chain around the strong-kick selector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 35) -> str:
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
    setup = block(lines, "CODE_84B951")
    wait = block(lines, "CODE_84B96B")
    selector = block(lines, "CODE_84B999")
    exit_handler = block(lines, "CODE_84B9C6")
    require(setup, "CODE_84:B951", "LDA.w #$05A0", "JSR.w CODE_84854E", "JSL.l CODE_8BA97A", "JSL.l CODE_83EF87", "LDA.w #DATA_82D69A", "JMP.w CODE_84E60C")
    require(wait, "CODE_84:B96B", "DEC.b $70", "BEQ.b CODE_84B972", "JMP.w CODE_84E641", "JSR.w CODE_848548", "LDA.w #$0018", "LDA.w #DATA_82CF9F", "JMP.w CODE_84E60C")
    require(selector, "CODE_84:B999", "DEC.b $70", "BEQ.b CODE_84B9A0", "JMP.w CODE_84E641", "LDA.w #$0008", "STA.b $70", "LDY.w #DATA_82D007", "LDY.w #DATA_82D100", "JMP.w CODE_84E600")
    require(exit_handler, "CODE_84:B9C6", "DEC.b $70", "JSL.l CODE_85EB3B", "JSR.w CODE_84E5D1", "JMP.w CODE_84878A")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "handler_table": "DATA_81:BD58", "entries": ["CODE_84:B951", "CODE_84:B96B", "CODE_84:B999", "CODE_84:B9C6"]},
        "known_records": [
            {"byte_offset": "$05A0", "handler": "CODE_84:B96B"},
            {"byte_offset": "$05A8", "handler": "CODE_84:B999"},
            {"byte_offset": "$05B0", "handler": "CODE_84:B9C6"},
        ],
        "proved_flow": [
            {"entry": "CODE_84:B951", "effect": "loads handler record $05A0 and dispatches DATA_82:D69A through CODE_84:E60C"},
            {"entry": "CODE_84:B96B", "condition": "$70 becomes zero", "effect": "CODE_84:8548 advances the current handler record from $05A0 to $05A8"},
            {"entry": "CODE_84:B999", "condition": "$70 becomes zero", "effect": "calls CODE_84:B9A0; its initial CODE_84:8548 advances the current handler record from $05A8 to $05B0, reloads $70 with $0008, and dispatches the D007/D100 selector"},
            {"entry": "CODE_84:B9C6", "condition": "CODE_84:E5D1 returns zero", "effect": "jumps to the common route CODE_84:878A after optionally calling CODE_85:EB3B when $70 is zero"},
        ],
        "limitations": [
            "The setup entry and D69A are not assigned a controller input or human-readable action name here.",
            "This control-flow proof does not validate visual frames, OAM composition, palette, or action outcome physics.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
