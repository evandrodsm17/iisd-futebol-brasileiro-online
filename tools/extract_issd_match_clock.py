#!/usr/bin/env python3
"""Extract the static USA-ROM match-clock tables from the disassembly.

The output preserves BCD words and the raw `$00A8` branch used by
CODE_A4:A4926F.  It intentionally does not assign half/extra-time semantics to
that branch without runtime evidence.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LABEL = re.compile(r"^(DATA_[0-9A-F]+):")
WORD = re.compile(r"\$([0-9A-F]{1,4})\b")


def table(lines: list[str], name: str, count: int) -> list[int]:
    try:
        start = lines.index(name + ":") + 1
    except ValueError as error:
        raise SystemExit(f"missing {name}") from error
    words: list[int] = []
    for line in lines[start:]:
        if LABEL.match(line):
            break
        if "dw" not in line:
            continue
        words.extend(int(value, 16) for value in WORD.findall(line))
        if len(words) >= count:
            return words[:count]
    raise SystemExit(f"{name} has {len(words)} words; expected {count}")


def bcd(value: int) -> str:
    return f"{value:04X}"


def routine_contains(lines: list[str], name: str, instruction: str) -> bool:
    try:
        start = lines.index(name + ":") + 1
    except ValueError as error:
        raise SystemExit(f"missing {name}") from error
    for line in lines[start:]:
        if LABEL.match(line):
            return False
        if line.strip() == instruction:
            return True
    return False


def routine_block(lines: list[str], name: str) -> str:
    try:
        start = lines.index(name + ":") + 1
    except ValueError as error:
        raise SystemExit(f"missing {name}") from error
    body: list[str] = []
    for line in lines[start:]:
        if LABEL.match(line):
            break
        body.append(line)
    return "\n".join(body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routine_asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.routine_asm.read_text(encoding="utf-8").splitlines()
    offsets = table(lines, "DATA_81AC83", 12)
    initial_zero = table(lines, "DATA_81E893", 4)
    initial_nonzero = table(lines, "DATA_81E89B", 4)
    if not routine_contains(lines, "CODE_83B02C", "STZ.w $00A8"):
        raise SystemExit("CODE_83B02C no longer clears $00A8")
    frame_gate = routine_block(lines, "CODE_A49401")
    for instruction in (
        "LDA.w $11FA",
        "ORA.w $00C0",
        "ORA.w $00B8",
        "ORA.w $00B6",
        "ORA.w $00BA",
        "BNE.b CODE_A49433",
        "INC.w !RAM_ISSD_InGame_GameTimerFrameCounter",
        "CMP.w #$003C",
        "SED",
        "JSR.w CODE_A493CC",
        "STZ.w !RAM_ISSD_InGame_GameTimerFrameCounter",
    ):
        if instruction not in frame_gate:
            raise SystemExit(f"CODE_A49401 no longer contains {instruction}")
    result = {
        "schema": "issd-match-clock/v2",
        "source": {
            "revision": "USA",
            "display_routine": "$83:C201",
            "initial_value_routine": "$A4:A4926F",
            "tick_routine": "$A4:93CC",
            "frame_counter_routine": "$A4:9401",
            "phase_offset_table": "$81:AC83",
            "initial_zero_table": "$81:E893",
            "initial_nonzero_table": "$81:E89B",
        },
        "facts": {
            "counter_frames_per_tick": 60,
            "encoding": "BCD",
            "frame_eligibility": {
                "entry": "$A4:9401",
                "blockers_orred": ["$11FA", "$00C0", "$00B8", "$00B6", "$00BA"],
                "rule": "the frame counter increments only when the OR of all five blocker words is zero",
                "tick": "at 60 eligible frames, the BCD timer is transformed by CODE_A4:93CC and the frame counter is cleared",
            },
            "phase_offset_table_bcd": {
                f"game_time_{index}": [bcd(value) for value in offsets[index * 4:(index + 1) * 4]]
                for index in range(3)
            },
            "initial_countdown_bcd": {
                "when_00a8_is_zero": [bcd(value) for value in initial_zero],
                "when_00a8_is_nonzero": [bcd(value) for value in initial_nonzero],
            },
            "match_initialization": {
                "routine": "$83:B02C",
                "writes_00a8": "0000",
                "initial_countdown_table": "when_00a8_is_zero",
            },
            "time_of_day_display_values": [3, 6, 9],
        },
        "limitations": [
            "The meaning of $00A8 and index 3 of the initial tables requires runtime validation.",
            "The phase index semantics and paused-frame behavior require runtime validation.",
            "This artifact must not by itself replace the browser clock policy.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted clock tables to {args.output}")


if __name__ == "__main__":
    main()
