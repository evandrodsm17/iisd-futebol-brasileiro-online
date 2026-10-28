"""Summarize a passive ISS Deluxe input/motion JSONL trace without naming inputs.

The trace is runtime evidence.  This tool reports observed masks and their
co-occurring actor values verbatim; it deliberately does not claim that a mask
is a particular SNES button or that a script is a football action.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED = {
    "frame", "joypad1", "held_p1", "pressed_p1", "selected_p1", "phase", "actor"
}
ACTOR_REQUIRED = {
    "state", "script", "descriptor", "direction", "x", "y", "vx", "vy",
    "timer", "duration", "cursor",
}


def load_trace(path: Path):
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
        if not REQUIRED <= row.keys() or not isinstance(row["actor"], dict):
            raise ValueError(f"{path}:{line_number}: missing top-level capture fields")
        if not ACTOR_REQUIRED <= row["actor"].keys():
            raise ValueError(f"{path}:{line_number}: missing actor capture fields")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no capture rows")
    return rows


def range_and_mean(values):
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def summarize_mask(rows):
    directions = Counter(row["actor"]["direction"] for row in rows)
    scripts = Counter(row["actor"]["script"] for row in rows)
    states = Counter(row["actor"]["state"] for row in rows)
    descriptors = Counter(row["actor"]["descriptor"] for row in rows)
    return {
        "frames": len(rows),
        "frame_span": [rows[0]["frame"], rows[-1]["frame"]],
        "directions": dict(sorted(directions.items())),
        "scripts": dict(sorted(scripts.items())),
        "states": dict(sorted(states.items())),
        "descriptors": dict(sorted(descriptors.items())),
        "vx": range_and_mean([row["actor"]["vx"] for row in rows]),
        "vy": range_and_mean([row["actor"]["vy"] for row in rows]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="capture_issd_input_motion.lua JSONL output")
    parser.add_argument("output", type=Path, help="JSON report path")
    args = parser.parse_args()

    rows = load_trace(args.trace)
    by_held = defaultdict(list)
    by_raw = defaultdict(list)
    by_pressed = defaultdict(list)
    for row in rows:
        by_held[row["held_p1"]].append(row)
        by_raw[row["joypad1"]].append(row)
        by_pressed[row["pressed_p1"]].append(row)

    payload = {
        "schema_version": 1,
        "source": {
            "kind": "passive_runtime_capture",
            "trace": str(args.trace).replace("\\", "/"),
            "capture_script": "tools/capture_issd_input_motion.lua",
            "fields": sorted(REQUIRED),
        },
        "sample_count": len(rows),
        "frame_span": [rows[0]["frame"], rows[-1]["frame"]],
        "observed_held_masks": {
            str(mask): summarize_mask(group)
            for mask, group in sorted(by_held.items())
        },
        "observed_raw_masks": {
            str(mask): summarize_mask(group)
            for mask, group in sorted(by_raw.items())
        },
        "observed_pressed_masks": {
            str(mask): summarize_mask(group)
            for mask, group in sorted(by_pressed.items())
        },
        "limitations": [
            "Masks are reported as observed integers; this report does not assign button names or polarities.",
            "Co-occurrence does not prove causal input-to-motion mapping; compare controlled capture segments before implementation.",
            "Actor state, script, descriptor and direction retain runtime numeric values until separately decoded.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"input/motion analysis: {len(rows)} samples, {len(by_held)} held masks")


if __name__ == "__main__":
    main()
