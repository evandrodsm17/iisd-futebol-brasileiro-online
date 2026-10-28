"""Extract statically visible writers of the shared ISSD $19D2 event word."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, count: int = 56) -> str:
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
    offside = block(lines, "CODE_80D680")
    foul = block(lines, "CODE_80F005")
    yellow = block(lines, "CODE_80F09E")
    card_tail = block(lines, "CODE_80F112")
    set_1000 = block(lines, "CODE_84BBF0")
    set_team_bit = block(lines, "CODE_85EC4D")
    clear_20 = block(lines, "CODE_85F8D6")
    reset = block(lines, "CODE_A4E082")
    require(offside, "CODE_80:D680", "LDA.w #$0400", "TSB.w $19D2")
    require(foul, "CODE_80:F005", "LDA.w #$0800", "TRB.w $19D2")
    require(yellow, "CODE_80:F09E", "LDA.w #$0800", "TSB.w $19D2")
    require(card_tail, "CODE_80:F112", "LDX.w #$0100", "TXA", "TSB.w $19D2")
    require(set_1000, "CODE_84:BBF0", "LDA.w #$1000", "STA.w $19D2")
    require(set_team_bit, "CODE_85:EC4D", "LDY.w #$4000", "LDY.w #$2000", "STY.w $19D2")
    require(clear_20, "CODE_85:F8D6", "LDA.w #$0020", "TRB.w $19D2")
    require(reset, "CODE_A4:E082", "STZ.w $19D0", "STZ.w $19D2", "STZ.w $19D4")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "word": "$7E:19D2"},
        "writers": [
            {"entry": "CODE_80:D680", "operation": "TSB", "mask": "$0400", "context": "called after a successful second CODE_80:D627 boundary result"},
            {"entry": "CODE_80:F005", "operation": "TRB", "mask": "$0800", "context": "foul-setting gate clears bit before further local tests"},
            {"entry": "CODE_80:F09E", "operation": "TSB", "mask": "$0800", "context": "yellow-card path sets bit only when its setting is zero"},
            {"entry": "CODE_80:F112", "operation": "TSB", "mask": "register X; immediate path loads $0100", "context": "card tail combines X into the word"},
            {"entry": "CODE_84:BBF0", "operation": "STA", "mask": "$1000", "context": "full replacement of the word"},
            {"entry": "CODE_85:EC4D", "operation": "STY", "mask": "$2000 or $4000", "context": "full replacement selected by local actor fields"},
            {"entry": "CODE_85:F8D6", "operation": "TRB", "mask": "$0020", "context": "clears bit during actor-flow setup"},
            {"entry": "CODE_A4:E082", "operation": "STZ", "mask": "$0000", "context": "global match-related reset also clears adjacent $19D0/$19D4"},
        ],
        "limitations": [
            "This is a writer index, not a complete read/consumer map; direct static reads were not located in the inspected assembly source.",
            "Bits must not be named after gameplay events based solely on nearby callers.",
            "The word is shared and also receives full replacements, so bit persistence across handlers requires runtime tracing.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
