"""Inventory statically visible calls to the non-default actor initializer entry."""

from __future__ import annotations

import argparse
import json
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
    sites = {
        "CODE_85:A2B4": block(lines, "CODE_85A2B4", 8),
        "CODE_85:AAF1": block(lines, "CODE_85AAF1", 20),
        "CODE_86:8499": block(lines, "CODE_868499", 9),
        "CODE_86:E2B7": block(lines, "CODE_86E2B7", 5),
        "CODE_86:E2BF": block(lines, "CODE_86E2BF", 7),
    }
    require(sites["CODE_85:A2B4"], "CODE_85:A2B4", "JSR.w CODE_85A0AA", "JSL.l CODE_868006")
    require(sites["CODE_85:AAF1"], "CODE_85:AAF1", "JSL.l CODE_868000", "JSL.l CODE_85AB5C", "JSL.l CODE_868006")
    require(sites["CODE_86:8499"], "CODE_86:8499", "LDX.b $1C", "LDY.b $1E", "JSL.l CODE_868006")
    require(sites["CODE_86:E2B7"], "CODE_86:E2B7", "LDX.w #$0010", "JSL.l CODE_868006")
    require(sites["CODE_86:E2BF"], "CODE_86:E2BF", "LDX.w #$0090", "JSL.l CODE_868006")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "callee": "CODE_86:8006", "call_site_count": 5},
        "call_sites": [
            {"entry": "CODE_85:A2B4", "register_setup": "calls CODE_85:A0AA immediately before; X/Y provenance requires that helper"},
            {"entry": "CODE_85:AAF1", "register_setup": "after a loop and CODE_85:AB5C; X/Y provenance remains contextual"},
            {"entry": "CODE_86:8499", "register_setup": "X=local $1C; Y=local $1E"},
            {"entry": "CODE_86:E2B7", "register_setup": "X=$0010; Y inherited"},
            {"entry": "CODE_86:E2BF", "register_setup": "X=$0090; Y inherited"},
        ],
        "limitations": [
            "Static call sites prove possible non-default Y flow but do not prove runtime values or player identity.",
            "The helper/caller contexts remain to be traced before associating the initialized actor with a gameplay entity.",
            "No call site alone makes actor+$0013 a direction, button, or velocity field.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
