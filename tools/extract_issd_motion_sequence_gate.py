"""Extract the native local motion-sequence progression gate."""

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
    gate = block(lines, "CODE_80DD9D", 17)
    selector = block(lines, "CODE_80DDB6", 7)
    require(gate, "CODE_80:DD9D/DD9F", "CODE_80DD9D:", "SEC", "RTL", "CODE_80DD9F:", "DEC.b $72", "BPL.b CODE_80DD9D", "LDA.b $64", "CMP.b $62", "BCS.b CODE_80DD9D", "LDA.b $66", "AND.w #$00FF", "STA.b $72", "INC.b $64", "CLC", "RTL")
    require(selector, "CODE_80:DDB6", "LDA.b $64", "ADC.w #$002B", "TAY", "RTL")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "gate": "CODE_80:DD9F", "selector": "CODE_80:DDB6"},
        "gate": {"timer": "decrement local $72", "hold": "when decremented $72 is nonnegative, return carry set", "limit": "when local $64 is greater than or equal to local $62, return carry set", "advance": "otherwise load local $72 from low byte of $66, increment local $64, return its value in A with carry clear"},
        "selector": "returns Y = local $64 + $002B",
        "limitations": [
            "The local fields are not named as frames, duration, speed, or an action sequence without caller/runtime correlation.",
            "Carry is preserved as a control-flow result; no browser animation state is changed from this fact alone.",
            "The selector offset $002B is a native value, not an exported pose index.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
