"""Extract the timer/result contract wrapped by CODE_84:E8A0."""

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
    wrapper = block(lines, "CODE_84E8A0", 4)
    timer = block(lines, "CODE_84E5D1", 30)
    require(wrapper, "CODE_84:E8A0", "JSR.w CODE_84E5D1", "RTL")
    require(timer, "CODE_84:E5D1", "DEC.b $16", "BNE.b CODE_84E5DC", "LDA.b $18", "BMI.b CODE_84E5DD", "LDA.w #$0000", "CODE_84E5DD:", "LDA.b $1A", "LSR", "LDA.w #$8000", "TSB.b $16", "LDA.b ($18),y", "AND.w #$FF00", "TRB.b $18", "CODE_84E5F9:", "TXA", "BRA.b CODE_84E651")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "wrapper": "CODE_84:E8A0", "entry": "CODE_84:E5D1", "continuation": "CODE_84:E651"},
        "timer_gate": {"counter": "local $16", "per_call": "decrements before testing", "nonzero_path": "returns immediately when decremented $16 is nonzero", "expired_nonnegative_script": "loads A=$0000 and returns", "expired_negative_script": "reads a word through local $18 indexed by local $1A >> 1"},
        "negative_script_path": {"sets": "bit $8000 in local $16", "word_handling": "keeps the fetched word in X; if its high byte is zero, clears bit $8000 in local $18; then passes the low byte to CODE_84:E68F via CODE_84:E651"},
        "limitations": [
            "The meanings of local $16, $18, and $1A are not promoted beyond their observed timer/script roles.",
            "A zero result is control-flow evidence only; it is not labeled animation completion without runtime correlation.",
            "The descriptor/action reached from CODE_84:E68F remains a separate OAM/VRAM evidence task.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
