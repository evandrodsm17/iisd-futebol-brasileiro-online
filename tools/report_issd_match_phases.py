"""Summarise observed ISSD phase, collision and trajectory dispatch indexes."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


FIELDS = ("phase", "collision_mode", "trajectory_left", "trajectory_right")


def transitions(rows: list[dict], field: str) -> list[dict]:
    result, previous = [], object()
    for row in rows:
        if field not in row:
            continue
        value = row[field]
        if value != previous:
            result.append({"frame": row["frame"], field: value})
            previous = value
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows, ignored = [], []
    for line_number, line in enumerate(args.trace.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            ignored.append(line_number)
    systems = {}
    for field in FIELDS:
        counts = Counter(row[field] for row in rows if field in row)
        systems[field] = {
            "samples_with_field": sum(counts.values()),
            "values": {str(value): count for value, count in sorted(counts.items())},
            "transitions": transitions(rows, field),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "evidence": "runtime-match-trace",
        "samples": len(rows),
        "ignored_malformed_lines": ignored,
        "systems": systems,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
