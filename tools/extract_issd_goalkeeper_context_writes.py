#!/usr/bin/env python3
"""Index goalkeeper dive-selector and `$1500` context writes in ISSD USA.

`$14A8` is a direct dive-mode selector.  In contrast, the nine-entry handler
table at DATA_83:DDA1 receives its index in A; CODE_83:DD99 only loads `$1500`
into Y as a context/base.  This tool intentionally keeps those roles separate.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


LABEL = re.compile(r"^(CODE_[0-9A-F]+):")
WRITE = re.compile(r"^\s*(ST[AZ])(?:\.[A-Za-z])?\s+(\$14A8|\$1500)(?:,([XxYy]))?\b")
IMMEDIATE_LOAD = re.compile(r"^\s*LDA\.[A-Za-z]\s+#\$([0-9A-F]+)\b")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routine_asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    writes: dict[str, list[dict[str, object]]] = defaultdict(list)
    routine = None
    previous = ""
    for line_number, line in enumerate(args.routine_asm.read_text(encoding="utf-8").splitlines(), 1):
        if match := LABEL.match(line):
            routine = match.group(1)
            previous = ""
            continue
        if not (match := WRITE.match(line)):
            if line.strip() and not line.lstrip().startswith(";"):
                previous = line
            continue
        instruction, address, index = match.groups()
        value: dict[str, str] = {"source": "runtime"}
        if instruction == "STZ":
            value = {"source": "zero", "value": "0000"}
        elif immediate := IMMEDIATE_LOAD.match(previous):
            value = {"source": "immediate", "value": immediate.group(1).zfill(4)}
        writes[address].append({
            "routine": routine,
            "line": line_number,
            "instruction": instruction,
            "addressing": "indexed" if index else "direct",
            "index": index.upper() if index else None,
            "assigned_value": value,
        })
        previous = line
    if not writes["$14A8"] or not writes["$1500"]:
        raise SystemExit("missing goalkeeper selector/context writes")
    result = {
        "schema": "issd-goalkeeper-context-writes/v1",
        "source": {"revision": "USA", "asm": args.routine_asm.name},
        "dive_selector": {"address": "$7E:14A8", "writes": writes["$14A8"]},
        "catch_dispatch": {
            "table": "$83:DDA1",
            "entry_count": 9,
            "index": "accumulator A at CODE_83:DD99",
            "context": "Y receives $7E:1500 at CODE_83:DD99",
            "context_writes": writes["$1500"],
        },
        "limitations": [
            "$1500 is dispatch context, not the catch selector itself.",
            "The index records explicit stores only; indexed context writes require runtime correlation.",
            "The semantic meaning of A values dispatched through DATA_83:DDA1 remains pending.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(writes['$14A8'])} dive and {len(writes['$1500'])} $1500 context writes")


if __name__ == "__main__":
    main()
