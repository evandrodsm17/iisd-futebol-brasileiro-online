"""Summarize a passive ISS Deluxe animation survey without naming unknown scripts."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED = {"frame", "phase", "selected_p1", "held_p1", "pressed_p1", "actor"}
ACTOR_REQUIRED = {
    "address", "state", "script", "descriptor", "pose", "direction", "x", "y",
    "timer", "duration", "cursor", "type", "kit_variant", "uniform_selector",
}


def load_rows(path: Path) -> list[dict]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("survey", type=Path, help="capture_issd_animation_survey.lua JSONL output")
    parser.add_argument("output", type=Path, help="JSON report path")
    args = parser.parse_args()

    rows = load_rows(args.survey)
    scripts = defaultdict(list)
    for row in rows:
        scripts[row["actor"]["script"]].append(row)

    observed = []
    for script, records in sorted(scripts.items()):
        actors = [row["actor"] for row in records]
        observed.append({
            "script": f"$82:{script:04X}",
            "observations": len(records),
            "frame_span": [min(row["frame"] for row in records), max(row["frame"] for row in records)],
            "directions": dict(sorted(Counter(actor["direction"] for actor in actors).items())),
            "descriptors": sorted({f"${actor['descriptor']:04X}" for actor in actors}),
            "states": dict(sorted(Counter(actor["state"] for actor in actors).items())),
            "actor_addresses": sorted({actor["address"] for actor in actors}),
            "phases": dict(sorted(Counter(row["phase"] for row in records).items())),
        })

    payload = {
        "schema_version": 1,
        "source": {
            "kind": "passive_runtime_animation_survey",
            "trace": str(args.survey).replace("\\", "/"),
            "capture_script": "tools/capture_issd_animation_survey.lua",
        },
        "sample_count": len(rows),
        "frame_span": [min(row["frame"] for row in rows), max(row["frame"] for row in rows)],
        "observed_scripts": observed,
        "limitations": [
            "The survey stores first observations only; it does not establish durations or full animation order.",
            "Script values without a static or same-frame visual match remain unnamed.",
            "No OAM, VRAM or CGRAM is present; this report cannot authorize a rendered sprite sheet.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"animation survey: {len(rows)} unique poses, {len(observed)} scripts")


if __name__ == "__main__":
    main()
