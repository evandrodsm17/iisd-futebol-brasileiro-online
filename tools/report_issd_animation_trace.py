"""Summarise observed ISS Deluxe animation states from a live JSONL trace."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    samples, malformed = [], []
    for number, line in enumerate(args.trace.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        try:
            samples.append(json.loads(line))
        except json.JSONDecodeError:
            malformed.append(number)

    groups: dict[int, dict] = defaultdict(lambda: {"samples": 0, "actors": set(), "states": Counter(), "directions": Counter(), "descriptors": Counter()})
    for sample in samples:
        for actor in sample.get("actors", []):
            script = actor.get("animation_script")
            if not isinstance(script, int):
                continue
            group = groups[script]
            group["samples"] += 1
            group["actors"].add(actor["address"])
            group["states"][actor.get("state", 0)] += 1
            group["directions"][actor.get("direction", -1)] += 1
            group["descriptors"][actor.get("descriptor", 0)] += 1

    report = {
        "evidence": "runtime-animation-trace",
        "valid_samples": len(samples),
        "ignored_malformed_lines": malformed,
        "scripts": [{
            "script": f"${script:04X}",
            "samples": group["samples"],
            "actors": [f"0x{actor:04X}" for actor in sorted(group["actors"])],
            "states": {f"${state:04X}": count for state, count in sorted(group["states"].items())},
            "directions": {str(direction): count for direction, count in sorted(group["directions"].items())},
            "descriptors": {f"${descriptor:04X}": count for descriptor, count in sorted(group["descriptors"].items())},
        } for script, group in sorted(groups.items())],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"{len(samples)} valid samples; {len(groups)} animation scripts")


if __name__ == "__main__":
    main()
