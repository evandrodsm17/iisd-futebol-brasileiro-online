#!/usr/bin/env python3
"""Index static readers and writers of in-game match-setting WRAM symbols.

The tool consumes the transfer manifest recovered from CODE_85:A456, then
searches the disassembly for the runtime destinations that have symbolic WRAM
names.  It deliberately reports instructions and routine labels, rather than
claiming the semantic effect of each branch.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


LABEL = re.compile(r"^(CODE_[0-9A-F]+):")
OPERAND = re.compile(r"^\s*([A-Z]{2,4})(?:\.[A-Za-z])?\s+(!RAM_ISSD_InGame_\w+)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routine_asm", type=Path)
    parser.add_argument("transfer_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    transfer = json.loads(args.transfer_manifest.read_text(encoding="utf-8"))
    symbols = {
        write["symbol"]
        for field in transfer["fields"]
        for write in field["writes"]
        if str(write["symbol"]).startswith("!RAM_ISSD_InGame_")
    }
    found: dict[str, list[dict[str, object]]] = defaultdict(list)
    label = None
    for number, line in enumerate(args.routine_asm.read_text(encoding="utf-8").splitlines(), 1):
        if match := LABEL.match(line):
            label = match.group(1)
            continue
        match = OPERAND.match(line)
        if not match or match.group(2) not in symbols:
            continue
        instruction, symbol = match.groups()
        found[symbol].append({
            "routine": label,
            "line": number,
            "instruction": instruction,
            "access": "write" if instruction.startswith("ST") else "read",
        })

    missing = sorted(symbols - found.keys())
    result = {
        "schema": "issd-match-setting-consumers/v1",
        "source": {"revision": "USA", "asm": args.routine_asm.name},
        "symbols": {symbol: found.get(symbol, []) for symbol in sorted(symbols)},
        "unreferenced_in_routine_macros": missing,
        "limitations": [
            "This is a static index of explicit symbolic operands.",
            "Indirect accesses and gameplay semantics require control-flow analysis or runtime capture.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {sum(map(len, found.values()))} accesses across {len(symbols)} runtime settings")


if __name__ == "__main__":
    main()
