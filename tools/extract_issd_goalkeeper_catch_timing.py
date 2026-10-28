#!/usr/bin/env python3
"""Extract the fixed byte/word records used by goalkeeper catch handlers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RECORD = re.compile(r"^(DATA_81B0(?:1C|1F|22|25|28|2B|2E)):\s*$")
VALUES = re.compile(r"\bdb \$([0-9A-F]{1,2})\s*:\s*dw \$([0-9A-F]{1,4})\b")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routine_asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records: dict[str, dict[str, object]] = {}
    current: tuple[str, int] | None = None
    for line_number, line in enumerate(args.routine_asm.read_text(encoding="utf-8").splitlines(), 1):
        if match := RECORD.match(line):
            current = (match.group(1), line_number)
            continue
        if not current or not (match := VALUES.search(line)):
            continue
        label, label_line = current
        records[label] = {
            "source": f"${label[5:7]}:{label[7:]}",
            "line": label_line,
            "counter_b6": int(match.group(1), 16),
            "indirect_value": f"{int(match.group(2), 16):04X}",
        }
        current = None
    if len(records) != 7:
        raise SystemExit(f"expected 7 catch records, found {len(records)}")
    result = {
        "schema": "issd-goalkeeper-catch-records/v1",
        "source": {"revision": "USA", "routine": "$83:DDB8", "asm": args.routine_asm.name},
        "records": records,
        "semantics": {
            "counter_b6": "First byte loaded into direct-page $B6 by CODE_83:DDB8.",
            "indirect_value": "Following word stored through both ($B8) and ($CE) by CODE_83:DDB8.",
        },
        "limitations": [
            "The records are not labeled as animation durations without runtime validation.",
            "The targets referenced by $B8 and $CE depend on the active goalkeeper page.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(records)} goalkeeper catch records to {args.output}")


if __name__ == "__main__":
    main()
