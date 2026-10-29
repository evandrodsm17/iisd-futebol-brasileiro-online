"""Inventory static writers of the shared $0408/$040C target pair."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LABEL = re.compile(r"^(CODE_[0-9A-F]+):")


def nearest_label(lines: list[str], index: int) -> str:
    for candidate in range(index, -1, -1):
        match = LABEL.match(lines[candidate])
        if match:
            return match.group(1).replace("CODE_", "CODE_")
    raise ValueError(f"writer at line {index + 1} has no preceding label")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    writers: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        if line.strip() != "STA.w $0408":
            continue
        window = lines[index + 1:index + 13]
        paired = any(candidate.strip() == "STA.w $040C" for candidate in window)
        writers.append({"assembly_line": index + 1, "entry": nearest_label(lines, index), "paired_040c_within_next_12_instructions": paired})
    pair_count = sum(bool(entry["paired_040c_within_next_12_instructions"]) for entry in writers)
    if len(writers) != 12 or pair_count != 11:
        raise ValueError("shared target writer inventory changed")
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "destinations": ["$0408", "$040C"], "writer_count": len(writers), "nearby_pair_count": pair_count},
        "writers": writers,
        "conclusion": "Eleven of twelve statically located writes to $0408 are paired with a nearby write to $040C; the remaining reset-like writer is CODE_83:FD6E. The destinations have multiple producers and are shared scratch state.",
        "limitations": [
            "The inventory does not assign a football meaning to individual producers or to the pair.",
            "A static writer list does not establish which producer is active in a specific match frame.",
            "Browser code must not treat this pair as a permanent ball or player coordinate source.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
