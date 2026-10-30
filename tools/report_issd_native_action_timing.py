"""Evidence-only action timing from BizHawk's native action OAM trace.

No inference of full animation duration: distinct descriptor transitions are
measured; final pose durations remain lower bounds.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median


def label(value: int) -> str:
    return "$" + format(value, "04X")


def records(path: Path) -> list[dict]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed record at line {lineno}") from exc
        actor = row.get("actor", {})
        if not isinstance(row.get("frame"), int) or not all(
            isinstance(actor.get(key), int)
            for key in ("address", "animation_script", "direction", "descriptor", "animation_cursor")
        ):
            raise ValueError(f"incomplete actor/frame at line {lineno}")
        rows.append(row)
    return sorted(rows, key=lambda row: (row["frame"], row["actor"]["address"]))


def runs(rows: list[dict], gap_limit: int = 25) -> list[list[dict]]:
    tracks = defaultdict(list)
    for row in rows:
        actor = row["actor"]
        tracks[(actor["address"], actor["animation_script"], actor["direction"])].append(row)
    result = []
    for track in tracks.values():
        active = []
        for row in track:
            if active and (
                row["frame"] - active[-1]["frame"] > gap_limit
                or row["actor"]["animation_cursor"] < active[-1]["actor"]["animation_cursor"]
            ):
                result.append(active)
                active = []
            active.append(row)
        if active:
            result.append(active)
    return sorted(result, key=lambda group: group[0]["frame"])


def summarize(group: list[dict]) -> dict:
    distinct = []
    for row in group:
        actor = row["actor"]
        if not distinct or distinct[-1]["descriptor"] != actor["descriptor"]:
            distinct.append({
                "descriptor": actor["descriptor"],
                "frame": row["frame"],
                "cursor": actor["animation_cursor"],
            })
    intervals = [
        distinct[i + 1]["frame"] - distinct[i]["frame"]
        for i in range(len(distinct) - 1)
    ]
    last_descriptor = distinct[-1]["descriptor"]
    end = max(
        row["frame"] for row in group
        if row["actor"]["descriptor"] == last_descriptor
    )
    actor = group[0]["actor"]
    return {
        "script": label(actor["animation_script"]),
        "direction": actor["direction"],
        "actor": "0x" + format(actor["address"], "04X"),
        "descriptors": [label(item["descriptor"]) for item in distinct],
        "cursor_sequence": [item["cursor"] for item in distinct],
        "first_frame": group[0]["frame"],
        "last_sampled_frame": group[-1]["frame"],
        "transition_intervals_frames": intervals,
        "last_pose_minimum_observed_frames": end - distinct[-1]["frame"] + 1,
        "exact_final_hold_known": False,
    }


def audit(rows: list[dict]) -> dict:
    tracks = [summarize(group) for group in runs(rows)]
    by_group = defaultdict(list)
    for track in tracks:
        by_group[(track["script"], track["direction"])].append(track)
    groups = []
    for (script, direction), tracks_for_group in sorted(by_group.items()):
        candidates = sorted(
            tracks_for_group, key=lambda t: len(t["descriptors"]), reverse=True
        )
        best = candidates[0]["descriptors"]
        intervals = []
        for i, descriptor in enumerate(best):
            samples = [
                track["transition_intervals_frames"][i]
                for track in tracks_for_group
                if i + 1 < len(track["descriptors"])
                and track["descriptors"][i] == descriptor
                and track["descriptors"][i + 1] == best[i + 1]
            ] if i + 1 < len(best) else []
            holds = [
                track["last_pose_minimum_observed_frames"]
                for track in tracks_for_group
                if track["descriptors"][-1] == descriptor
            ] if i == len(best) - 1 else []
            intervals.append({
                "descriptor": descriptor,
                "samples": samples,
                "measured_transition_frames": int(median(samples)) if samples else None,
                "last_pose_lower_bounds": holds,
                "preview_frames_not_rom_timing": (
                    int(median(samples)) if samples else max(4, max(holds, default=4))
                ),
                "status": "observed-transition" if samples else "unverified",
            })
        groups.append({
            "script": script,
            "direction": direction,
            "observed_runs": len(tracks_for_group),
            "descriptors": best,
            "timing": intervals,
            "runs": tracks_for_group,
        })
    return {
        "schema": "issd-native-action-timing-audit/v1",
        "source_evidence": "same-frame BizHawk native action OAM trace",
        "total_records": len(rows),
        "run_count": len(tracks),
        "groups": groups,
        "limitations": [
            "Capture is deduplicated; not every emulator frame is included.",
            "First pose can start earlier than its first captured frame.",
            "No observation proves exact end of the sixth pose.",
            "Preview frame counts must not be promoted to final ROM-equivalent timing.",
            "D100 is associated with LowKick artwork but not proven to mean pass.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit(records(args.trace))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Analyzed {report['total_records']} records / {report['run_count']} runs / {len(report['groups'])} script-directions")


if __name__ == "__main__":
    main()
