"""Extract the native handler chain that begins at the slide descriptor table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 46) -> str:
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
    setup = block(lines, "CODE_84A056")
    handler = block(lines, "CODE_84A08D", 75)
    return_path = block(lines, "CODE_849FC1")
    completion = block(lines, "CODE_849FD7")
    require(setup, "CODE_84:A056", "LDA.w #$000C", "STA.b $70", "LDA.w #$0008", "STA.b $72", "LDA.w #DATA_82DB25", "LDY.w #DATA_82EA28", "JSR.w CODE_84E60C", "LDA.w #$02D0", "JMP.w CODE_84854E")
    require(handler, "CODE_84:A08D", "JSR.w CODE_84A1A2", "DEC.b $70", "JSR.w CODE_84E5D1", "BEQ.b CODE_84A117", "CODE_84A117:", "JMP.w CODE_849FC1")
    require(return_path, "CODE_84:9FC1", "LDY.w #$0004", "LDA.w #DATA_82DB5B", "LDY.w #DATA_82E571^$8000", "JSR.w CODE_84E60C", "LDA.w #$02F8", "JMP.w CODE_84854E")
    require(completion, "CODE_84:9FD7", "JSR.w CODE_84E5D1", "BEQ.b CODE_849FDD", "JSL.l CODE_80D7AB", "JMP.w CODE_848DD1", "JMP.w CODE_84878A")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "handler_table": "DATA_81:BD58", "entries": ["CODE_84:A056", "CODE_84:A08D", "CODE_84:9FC1", "CODE_84:9FD7"]},
        "known_records": [
            {"byte_offset": "$02D0", "handlers": ["CODE_84:A08D", "CODE_84:A08B", "CODE_84:A08D"]},
            {"byte_offset": "$02F8", "handlers": ["CODE_84:9FD7", "CODE_84:9FD7", "CODE_84:9FD7"]},
        ],
        "proved_flow": [
            {"entry": "CODE_84:A056", "effect": "dispatches DATA_82:DB25 through CODE_84:E60C and installs record $02D0"},
            {"entry": "CODE_84:A08D", "condition": "its CODE_84:E5D1 check returns zero", "effect": "jumps to CODE_84:9FC1"},
            {"entry": "CODE_84:9FC1", "effect": "dispatches DATA_82:DB5B through CODE_84:E60C and installs record $02F8"},
            {"entry": "CODE_84:9FD7", "condition": "its CODE_84:E5D1 check returns zero", "effect": "branches by $00A6 to CODE_84:8DD1 or CODE_84:878A"},
        ],
        "limitations": [
            "The caller of CODE_84:A056 is not mapped to a controller button or a complete gameplay predicate.",
            "The condition returned by CODE_84:E5D1 and the semantic role of $00A6 are not named here.",
            "This control flow does not prove the full pose composition or action-result physics.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
