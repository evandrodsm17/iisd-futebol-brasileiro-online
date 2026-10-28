#!/usr/bin/env python3
"""Validate the static ISSD foul-setting and card-setting gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def window(lines: list[str], label: str, length: int = 180) -> str:
    start = next(index for index, line in enumerate(lines) if line.strip() == f"{label}:")
    return "\n".join(lines[start : start + length])


def verify(body: str, label: str, *fragments: str) -> None:
    for fragment in fragments:
        if fragment not in body:
            raise SystemExit(f"{label} no longer contains expected instruction: {fragment}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    first = window(lines, "CODE_80EED3")
    second = window(lines, "CODE_80EF83")
    final = window(lines, "CODE_80F005")
    common_exit = window(lines, "CODE_80F125", 55)
    setting = "!RAM_ISSD_InGame_CurrentFoulSetting"
    verify(first, "CODE_80EED3", setting, "BEQ.b CODE_80EEEC", "LDA.w $11F9", "BPL.b CODE_80EEEC", "LDA.w #$0200", "STA.w $006E,x")
    verify(second, "CODE_80EF83", setting, "BNE.b CODE_80EFA2", "LDA.w #$0200", "TSB.b $6E", "LDA.w #$8003")
    verify(final, "CODE_80F005", "TRB.w $19D2", setting, "BNE.b CODE_80F045", "!RAM_ISSD_InGame_CurrentYellowCardSetting", "LDA.w #$0800", "TSB.w $19D2")
    verify(common_exit, "CODE_80F125", "TRB.w $04DE", "LDY.w #$0003", "LDY.w #$0006", "STY.w $00BA", "STA.w $00C4", "STA.w $00C6", "SEC")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "routines": ["CODE_80:EED3", "CODE_80:EF83", "CODE_80:F005"]},
        "foul_setting_gates": [
            {"entry": "CODE_80:EED3", "observed": "when actor 0068 is zero, actor 006C has bit 0100 clear, foul setting is zero, and 11F9 is negative, returns CLC; otherwise continues to local/actor checks"},
            {"entry": "CODE_80:EF83", "observed": "in the 0030==1 and negative-11F9 path, non-zero foul setting branches directly to code that sets local 6E bit 0200 and stores 8003 in local 78"},
            {"entry": "CODE_80:F005", "observed": "after clearing 19D2 bit 0800, non-zero foul setting returns CLC at F045 before the subsequent event/card branches"},
        ],
        "card_setting_gates": [
            {"entry": "CODE_80:F076", "observed": "non-zero yellow-card setting jumps to F125"},
            {"entry": "CODE_80:F09E", "observed": "non-zero yellow-card setting jumps to F125; zero sets 19D2 bit 0800 before helper calls"},
        ],
        "common_exit": {
            "entry": "CODE_80:F125",
            "observed": "clears 04DE bit 0800; writes 00BA as 0003 or 0006 depending on 0DD0 bits 1800; copies local 76 to 00C4; clears 00C6; returns SEC after three CODE_80:D5D3 calls",
        },
        "limitations": [
            "The setting values are control inputs within larger state and flag predicates; they are not a standalone enabled/disabled truth table.",
            "Carry results and the behavior of called helpers remain unresolved without runtime traces.",
            "The values 0003/0006 in 00BA are internal values, not named restart or referee phases.",
            "No web foul, card, restart, or referee behavior is derived from this artifact.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("foul gates: OK (3 foul entries, 2 card entries)")


if __name__ == "__main__":
    main()
