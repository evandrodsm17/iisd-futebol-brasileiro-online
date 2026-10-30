"""Audit ISS Deluxe action sprite evidence without inventing poses or timing.

Static descriptor tables list candidates, not an action's playback timing.
Runtime summary counts are not direction-specific; only raw traces can prove
which descriptor occurred in a given direction and frame.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def hex16(value: int) -> str:
    return f"${value:04X}"


def parse_script(value: str) -> int:
    """Accept $82:D007, $D007 and 0xD007 identifiers."""
    part = value.split(":")[-1].strip()
    if part.startswith("$"):
        return int(part[1:], 16)
    return int(part, 16) if any(ch in "ABCDEFabcdef" for ch in part) else int(part, 0)


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL {path}:{line_number}: {error.msg}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected object at {path}:{line_number}")
            yield record


def actors(record: dict):
    if isinstance(record.get("actor"), dict):
        return (record["actor"],)
    return record.get("actors", [])


def collect_runtime(traces: list[Path]):
    observed = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    for path in traces:
        for record in read_jsonl(path):
            frame = record.get("frame")
            for actor in actors(record):
                script, direction, descriptor = (
                    actor.get("animation_script"), actor.get("direction"), actor.get("descriptor")
                )
                if all(isinstance(value, int) and not isinstance(value, bool) for value in (script, direction, descriptor)):
                    observed[script][direction][descriptor].add((str(path), frame))
    return observed


def capture_is_complete(record: dict, path: Path) -> bool:
    """Require complete same-frame evidence files before claiming renderability."""
    actor = record.get("actor")
    if not isinstance(actor, dict) or not actor.get("parts") or not isinstance(record.get("obsel"), int):
        return False
    # Packed/static action geometry uses a different format from WRAM planes.
    if actor.get("pose", 0) >= 0x8000 or actor.get("geometry_source") == "static-packed-unresolved":
        return False
    if any(abs(part.get(axis, 0)) > 128 for part in actor["parts"] for axis in ("x", "y")):
        return False
    for key, expected in (("vram", 0x10000), ("cgram", None)):
        raw_path = record.get(key)
        if not isinstance(raw_path, str) or not raw_path:
            return False
        file_path = Path(raw_path)
        if not file_path.is_absolute():
            file_path = path.parent / file_path
        if not file_path.is_file():
            return False
        if key == "vram":
            if file_path.stat().st_size != expected:
                return False
        else:
            try:
                decoded = bytes.fromhex("".join(file_path.read_text(encoding="utf-8").split()))
            except (UnicodeError, ValueError):
                return False
            if len(decoded) != 0x200:
                return False
    return True


def collect_captures(paths: list[Path]):
    observations = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    renderable = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    invalid = []
    for path in paths:
        for record in read_jsonl(path):
            actor = record.get("actor", {})
            script, direction, descriptor = (
                actor.get("animation_script"), actor.get("direction"), actor.get("descriptor")
            )
            if not all(isinstance(value, int) and not isinstance(value, bool) for value in (script, direction, descriptor)):
                invalid.append({
                    "trace": str(path), "frame": record.get("frame"),
                    "reason": "missing script/direction/descriptor",
                })
                continue
            key = (str(path), record.get("frame"))
            observations[script][direction][descriptor].add(key)
            if capture_is_complete(record, path):
                renderable[script][direction][descriptor].add(key)
            else:
                invalid.append({
                    "trace": str(path), "frame": record.get("frame"),
                    "script": hex16(script), "direction": direction,
                    "descriptor": hex16(descriptor),
                    "reason": "missing/invalid OAM geometry, OBJSEL or same-frame VRAM/CGRAM",
                })
    return observations, renderable, invalid


def aggregate_reports(paths: list[Path]):
    counts = defaultdict(Counter)
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for script in payload.get("scripts", []):
            script_id = parse_script(script["script"])
            for descriptor, count in script.get("descriptors", {}).items():
                counts[script_id][parse_script(descriptor)] += count
    return counts


def lowkick_assets(path: Path | None):
    matches = defaultdict(list)
    if path is None:
        return matches
    payload = json.loads(path.read_text(encoding="utf-8"))
    for script in payload.get("scripts", []):
        script_id = parse_script(script["script"])
        for frame in script.get("frames", []):
            asset = frame.get("asset") or ""
            if "_LowKick" in asset:
                matches[script_id].append({
                    "descriptor": frame["descriptor"], "asset": asset,
                    "observed_samples": frame.get("samples", 0),
                })
    return matches


def sorted_ids(values):
    return [hex16(value) for value in sorted(values)]


def build_report(static: dict, summaries: dict, runtime: dict, capture: dict,
                 renderable: dict, invalid: list, assets: dict,
                 has_runtime: bool, has_capture: bool) -> dict:
    actions = []
    for name, action in static["actions"].items():
        script_id = parse_script(action["script"])
        directions = []
        for entry in action["directions"]:
            direction = entry["direction"]
            static_sequence = entry["descriptors"]
            expected = set(static_sequence)
            runtime_seen = set(runtime.get(script_id, {}).get(direction, {})) if has_runtime else set()
            captured = set(capture.get(script_id, {}).get(direction, {})) if has_capture else set()
            complete = set(renderable.get(script_id, {}).get(direction, {})) if has_capture else set()
            directions.append({
                "direction": direction,
                "static_entries_including_repeats": len(static_sequence),
                "static_candidate_descriptors": sorted_ids(expected),
                "runtime_observed": sorted_ids(runtime_seen) if has_runtime else None,
                "runtime_missing_candidates": sorted_ids(expected - runtime_seen) if has_runtime else None,
                "runtime_outside_static_table": sorted_ids(runtime_seen - expected) if has_runtime else None,
                "same_frame_capture_observed": sorted_ids(captured) if has_capture else None,
                "same_frame_renderable": sorted_ids(complete) if has_capture else None,
                "capture_missing_candidates": sorted_ids(expected - complete) if has_capture else None,
            })
        actions.append({
            "name": name,
            "script": action["script"],
            "aggregate_observed_descriptors_all_directions": sorted_ids(summaries.get(script_id, {})),
            "aggregate_sample_count_all_reports": sum(summaries.get(script_id, {}).values()),
            "lowkick_asset_matches": assets.get(script_id, []),
            "directions": directions,
        })
    return {
        "evidence": "static-rom-script-table-and-observed-runtime-data",
        "sources": {
            "raw_runtime_traces_provided": has_runtime,
            "same_frame_captures_provided": has_capture,
        },
        "limitations": [
            "Static descriptor entries may repeat or include transitions; they do not establish animation duration or final frame order.",
            "Aggregate trace reports contain no descriptor-by-direction relationship; direction fields remain null without raw JSONL.",
            "Same-frame renderability confirms presence of full VRAM/CGRAM and OAM, not pixel equivalence with a ROM reconstruction.",
            "LowKick graphics indicate visual assets only; they do not identify a gameplay pass or shot button.",
        ],
        "incomplete_captures": invalid,
        "actions": actions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", type=Path, default=Path("dist/data/issd-action-scripts.json"))
    parser.add_argument("--report", type=Path, action="append", default=[], help="existing aggregate report (repeatable)")
    parser.add_argument("--trace", type=Path, action="append", default=[], help="raw match trace JSONL (repeatable)")
    parser.add_argument("--capture", type=Path, action="append", default=[], help="same-frame VRAM JSONL (repeatable)")
    parser.add_argument("--asset-map", type=Path, default=None, help="resolved asset map, for LowKick evidence")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    observations, renderable, incomplete = collect_captures(args.capture)
    report = build_report(
        json.loads(args.static.read_text(encoding="utf-8")),
        aggregate_reports(args.report),
        collect_runtime(args.trace),
        observations, renderable, incomplete,
        lowkick_assets(args.asset_map), bool(args.trace), bool(args.capture),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Checked {len(report['actions'])} action script families; {len(incomplete)} incomplete same-frame captures.")


if __name__ == "__main__":
    main()
