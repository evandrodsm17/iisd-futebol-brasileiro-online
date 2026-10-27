"""Summarise captured ISSD one-shot action timing without inferring a cycle."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


TIMING_FIELDS = ("animation_handler", "animation_timer", "animation_duration", "animation_cursor")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="issd-action-vram-trace.jsonl")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    grouped: dict[tuple[int, int, int], list[dict]] = defaultdict(list)
    missing = 0
    for line_number, line in enumerate(args.trace.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        row = json.loads(line)
        actor = row.get("actor", {})
        if not all(field in actor for field in TIMING_FIELDS):
            missing += 1
            continue
        grouped[(actor["animation_script"], actor["direction"], actor["descriptor"])].append({
            "frame": row["frame"],
            **{field: actor[field] for field in TIMING_FIELDS},
        })
    poses = []
    for (script, direction, descriptor), observations in sorted(grouped.items()):
        poses.append({
            "script": f"$82:{script:04X}",
            "direction": direction,
            "descriptor": f"${descriptor:04X}",
            "observations": observations,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "evidence": "runtime-action-vram-trace",
        "poses": poses,
        "records_without_timing_fields": missing,
        "limitations": "Observations are reported verbatim; no duration or pose-order inference is performed.",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
