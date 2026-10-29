"""Extract the byte-overlap boundary around actor offset $0013."""

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
    initializer = block(lines, "CODE_868000", 33)
    gate = block(lines, "CODE_80DD31", 16)
    require(initializer, "CODE_86:8000", "LDX.w #$0000", "LDY.w #$0000", "CODE_868006:", "JSR.w CODE_868036", "STZ.w $0014,x", "CODE_868036:", "TYA", "STA.w $0012,x")
    require(gate, "CODE_80:DD31", "LDA.w $0013,x", "AND.w #$000F")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "default_initializer": "CODE_86:8000", "direct_initializer_entry": "CODE_86:8006", "field_writer": "CODE_86:8036", "consumer": "CODE_80:DD31"},
        "layout": {"architecture": "65C816 little-endian 16-bit accumulator mode at these instructions", "word_at_actor_plus_0012": ["byte +$0012 (low)", "byte +$0013 (high)"], "word_at_actor_plus_0013": ["byte +$0013 (low)", "byte +$0014 (high)"], "consumer_mask": "CODE_80:DD31 reads word actor+$0013 then masks $000F, therefore it observes the low nibble of byte +$0013"},
        "initialization": {"default_wrapper": "CODE_86:8000 explicitly sets Y=$0000 before entering CODE_86:8006", "direct_entry": "CODE_86:8006 retains caller Y", "actor_plus_0012": "Y via TYA / STA.w $0012,x", "actor_plus_0014": "$0000 via STZ.w $0014,x", "deduction": "the default wrapper initializes the consumed byte +$0013 to zero; direct entry can initialize it from the caller-Y high byte"},
        "limitations": [
            "This establishes byte overlap and initialization only, not the semantic meaning of Y or the resulting nibble.",
            "Other writers of the byte range remain to be traced before lifecycle or input meaning can be assigned.",
            "No browser behavior is changed from this structural result alone.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
