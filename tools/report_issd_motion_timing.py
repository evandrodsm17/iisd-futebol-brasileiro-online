"""Recover observed hold times for validated ISS Deluxe locomotion descriptors.

The natural trace is sampled every other emulated frame.  This reports how
long each known locomotion descriptor remains active for a single actor before
it changes.  It does not infer missing frames or animation order.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


CYCLES = {
    "walking": (0xCEF8, [0xA48B, 0xA4E5, 0xA53F, 0xA4E5, 0xA48B, 0xA431, 0xA3D7, 0xA431], 10),
    "running": (0xCF9F, [0xA749, 0xA791, 0xA7D9, 0xA791, 0xA749, 0xA701, 0xA6B9, 0xA701], 8),
}


def summary(values: list[int]) -> dict[str, int] | None:
    if not values:
        return None
    values = sorted(values)
    return {
        "observations": len(values),
        "min": values[0],
        "median": values[(len(values) - 1) // 2],
        "p95": values[round((len(values) - 1) * 0.95)],
        "max": values[-1],
    }


def descriptor_index(family: str, direction: int, descriptor: int) -> int | None:
    _, bases, frame_count = CYCLES[family]
    base = bases[direction]
    offset = descriptor - base
    if offset < 0 or offset % 9 or offset // 9 >= frame_count:
        return None
    return offset // 9


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    active: dict[int, tuple[str, int, int, int]] = {}
    holds: dict[tuple[str, int, int], list[int]] = defaultdict(list)
    discarded_gaps = 0
    last_frame = 0

    def close(address: int, end_frame: int) -> None:
        family, direction, index, start = active.pop(address)
        duration = end_frame - start
        if duration > 0:
            holds[(family, direction, index)].append(duration)

    for raw in args.trace.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        frame = row["frame"]
        last_frame = frame
        seen: set[int] = set()
        for actor in row.get("actors", []):
            address = actor["address"]
            seen.add(address)
            family = next((name for name, (script, _, _) in CYCLES.items() if actor.get("animation_script") == script), None)
            direction = actor.get("direction")
            index = descriptor_index(family, direction, actor["descriptor"]) if family and isinstance(direction, int) and 0 <= direction <= 7 else None
            previous = active.get(address)
            current = (family, direction, index) if index is not None else None
            if previous is not None and (current is None or previous[:3] != current):
                close(address, frame)
            if current is not None and address not in active:
                active[address] = (*current, frame)
        # An actor that disappears cannot have its hold time extended across an
        # unknown gap.  Close it at this sample boundary instead.
        for address in list(active):
            if address not in seen:
                close(address, frame)
                discarded_gaps += 1

    for address in list(active):
        close(address, last_frame + 2)

    families: dict[str, dict[str, object]] = {}
    for family, (_, _, frame_count) in CYCLES.items():
        directions: dict[str, object] = {}
        for direction in range(8):
            directions[str(direction)] = {
                str(index): summary(holds[(family, direction, index)])
                for index in range(frame_count)
            }
        families[family] = directions

    payload = {
        "source": str(args.trace).replace("\\", "/"),
        "unit": "emulated frames between trace samples; no browser timing conversion applied",
        "discarded_actor_gaps": discarded_gaps,
        "families": families,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
