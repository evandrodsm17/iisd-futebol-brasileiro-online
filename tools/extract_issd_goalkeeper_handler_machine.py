"""Extract the two static goalkeeper dispatch machines from ISSD USA assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def table(lines: list[str], label: str) -> list[str]:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    result = []
    for line in lines[start + 1:]:
        line = line.strip()
        if not line.startswith("dw CODE_"):
            break
        result.append(line.removeprefix("dw "))
    return result


def block(lines: list[str], label: str, length: int = 100) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + length])


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
    modes = table(lines, "DATA_83DCAA")
    catches = table(lines, "DATA_83DDA1")
    if modes != ["CODE_83DCE6", "CODE_83DD05", "CODE_83DD6E"]:
        raise ValueError(f"unexpected goalkeeper mode table: {modes}")
    if catches != ["CODE_83DDB3", "CODE_83DDC8", "CODE_83DE20", "CODE_83DE2A", "CODE_83DE88", "CODE_83DE92", "CODE_83DE99", "CODE_83DEA5", "CODE_83DEAC"]:
        raise ValueError(f"unexpected goalkeeper catch table: {catches}")
    require(block(lines, "CODE_83DCA2"), "CODE_83:DCA2", "$14A8", "DATA_83DCAA")
    require(block(lines, "CODE_83DD05"), "CODE_83:DD05", "#$0D00", "#$0E00", "JSR.w CODE_83DD14")
    require(block(lines, "CODE_83DD6E"), "CODE_83:DD6E", "$1522", "JSR.w CODE_83DD83")
    require(block(lines, "CODE_83DD99"), "CODE_83:DD99", "#$1500", "DATA_83DDA1")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "mode_dispatch": "DATA_83:DCAA", "catch_dispatch": "DATA_83:DDA1"},
        "mode_machine": {
            "selector": "$7E:14A8 at CODE_83:DCA2",
            "entries": [
                {"index": 0, "entry": "CODE_83:DCE6", "observed_effect": "immediate return"},
                {"index": 1, "entry": "CODE_83:DD05", "observed_effect": "runs CODE_83:DD14 for direct pages $0D00 and $0E00"},
                {"index": 2, "entry": "CODE_83:DD6E", "observed_effect": "conditionally runs CODE_83:DD83 for $0D00/$0E00 using $1522"},
            ],
        },
        "catch_machine": {
            "selector": "accumulator A at CODE_83:DD99; $1500 is loaded into Y as context",
            "entries": [{"index": index, "entry": entry} for index, entry in enumerate(catches)],
            "observed_fields": ["$B2", "$B4", "$B6", "$B8", "$BA", "$BC", "$BE", "$CE", "$F6"],
            "record_writer": "CODE_83:DDB8 loads DATA_81:B01C-family records into $B6 and through ($B8)/($CE)",
        },
        "limitations": [
            "Dispatch indexes are native control values, not labels for named goalkeeper moves.",
            "The $1500 context must not be treated as the catch selector.",
            "Visual animation, ball possession semantics, and browser controls require runtime correlation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
