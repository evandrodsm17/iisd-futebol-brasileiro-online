"""Extract the dynamic target-offset scheduler at CODE_80:DEAA..DF1D."""

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
    initializer = block(lines, "CODE_80DEAA", 11)
    loader = block(lines, "CODE_80DEB9", 49)
    scheduler = block(lines, "CODE_80DF00", 30)
    selector = block(lines, "DATA_819623", 3)
    require(initializer, "CODE_80:DEAA", "STZ.b $76", "STZ.b $78", "STZ.b $7A", "LDA.w #DATA_819842", "JSL.l CODE_80DEB9", "BRA.b CODE_80DF1D")
    require(loader, "CODE_80:DEB9", "ADC.b $76", "ADC.w #$0020", "LDA.w DATA_819623,x", "AND.w #$001F", "LDA.b ($40),y", "DEC.b $79", "LDA.b ($42),y", "DEC.b $7B", "ASL.b $44", "EOR.w #$FFFF", "STA.b $78", "STA.b $7A", "RTL")
    require(scheduler, "CODE_80:DF00", "DEC.b $70", "LDA.w #$0004", "LDA.b $76", "INC", "CMP.w #$0008", "LDA.w #$0000", "LDA.w #DATA_819842", "JSL.l CODE_80DEB9", "CODE_80DF1D:", "ADC.b $08", "STA.w $0408", "STA.w $1BC8", "ADC.b $0C", "STA.w $040C", "STA.w $0412", "STA.w $1BCC", "RTL")
    require(selector, "DATA_81:9623", "db $00,$08,$10,$98,$80,$C8")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "initializer": "CODE_80:DEAA", "loader": "CODE_80:DEB9", "scheduler": "CODE_80:DF00", "writer": "CODE_80:DF1D", "data_base": "DATA_81:9842"},
        "initialization": "sets local $70=$0004; clears local $76/$78/$7A; loads offsets through CODE_80:DEB9; writes through CODE_80:DF1D",
        "loader": {"rows": "uses base + local $76 and base + local $76 + $0020", "selector": "DATA_81:9623[local $2E] masked with $001F", "outputs": "reads signed bytes into local $78/$7A, then conditionally two's-complement negates each according to two successive ASL operations on local $44", "selector_bytes": ["$00", "$08", "$10", "$98", "$80", "$C8"]},
        "scheduler": "each call decrements local $70; when it reaches zero, reloads $0004, increments local $76 modulo $0008, and reloads offsets",
        "writer": {"$0408": "local $78 + local $08", "$040C": "local $7A + local $0C", "mirrors": ["$1BC8", "$0412", "$1BCC"]},
        "limitations": [
            "The rows and selector bits are preserved structurally; they are not named as an animation, camera, or football effect.",
            "The local $44 condition bits are not assigned a flip/direction meaning.",
            "The shared targets remain scratch state, not a permanent entity position.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
