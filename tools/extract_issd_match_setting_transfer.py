#!/usr/bin/env python3
"""Recover the ROM-USA menu-to-match setting transfer at CODE_85A456.

This is intentionally a static extractor.  It reads the local disassembly,
records only the selected WRAM symbols loaded in the initialization routine and
the destinations written before the next selected value is loaded.  It does
not assign gameplay behaviour to those fields.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROUTINE = "CODE_85A456:"
END = "CODE_85A51F:"
LOAD = re.compile(r"^\s*LDA\.w (!RAM_ISSD_MainMenu_Selected\w+)")
STORE = re.compile(r"^\s*STA\.w ([!$A-Za-z0-9_]+)")
RAM = re.compile(r"^(!RAM_ISSD_\w+)\s*=\s*(\$[0-9A-F]+)")


def normalise_address(value: str, ram_symbols: dict[str, str]) -> str:
    if value in ram_symbols:
        return f"$7E:{int(ram_symbols[value][1:], 16):04X}"
    if value.startswith("$"):
        return f"$7E:{int(value[1:], 16):04X}"
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routine_asm", type=Path)
    parser.add_argument("ram_map", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    ram_symbols = {
        match.group(1): match.group(2)
        for line in args.ram_map.read_text(encoding="utf-8").splitlines()
        if (match := RAM.match(line))
    }
    lines = args.routine_asm.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(ROUTINE) + 1
        stop = lines.index(END, start)
    except ValueError as error:
        raise SystemExit(f"missing transfer range {ROUTINE}..{END}") from error

    fields: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line_number, line in enumerate(lines[start:stop], start + 1):
        if match := LOAD.match(line):
            if current:
                fields.append(current)
            symbol = match.group(1)
            current = {
                "selected_symbol": symbol,
                "selected_wram": normalise_address(symbol, ram_symbols),
                "load_line": line_number,
                "writes": [],
            }
            continue
        if current and (match := STORE.match(line)):
            destination = match.group(1)
            current["writes"].append({
                "symbol": destination,
                "wram": normalise_address(destination, ram_symbols),
                "line": line_number,
            })
    if current:
        fields.append(current)

    # The menu routine transfers the ten documented match settings plus sound
    # and the unused announcer-enable flag.  Keeping all twelve preserves the
    # routine boundary instead of silently discarding real ROM writes.
    if len(fields) != 12:
        raise SystemExit(f"expected 12 selected setting transfers, found {len(fields)}")

    result = {
        "schema": "issd-match-setting-transfer/v1",
        "source": {"revision": "USA", "routine": "$85:A456"},
        "fields": fields,
        "limitations": [
            "Writes record storage transfer and normalization flow only.",
            "No browser rule or visual effect is inferred from a write alone.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(fields)} match setting transfers to {args.output}")


if __name__ == "__main__":
    main()
