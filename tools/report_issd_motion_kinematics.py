"""Summarise observed ISS Deluxe walk/run kinematics without rescaling them.

The BizHawk trace stores actor coordinates and velocity words.  This tool keeps
those values in native units and reports position deltas between adjacent trace
samples for the same actor.  It deliberately does not convert the result to
Canvas units: that conversion needs a separately validated field projection.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


SCRIPTS = {0xCEF8: "walking", 0xCF9F: "running"}


def quantiles(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)

    def at(percent: float) -> float:
        return ordered[round((len(ordered) - 1) * percent)]

    return {"min": at(0), "p25": at(0.25), "median": at(0.5), "p75": at(0.75), "p95": at(0.95), "max": at(1)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--selected-p1-only",
        action="store_true",
        help="only include the actor referenced by selected_p1 in each trace row",
    )
    args = parser.parse_args()

    previous: dict[int, tuple[int, int, int, str, int]] = {}
    deltas: dict[tuple[str, int], list[float]] = defaultdict(list)
    velocities: dict[tuple[str, int], list[float]] = defaultdict(list)
    samples: dict[tuple[str, int], int] = defaultdict(int)
    rejected = 0

    for raw in args.trace.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        record = json.loads(raw)
        frame = record["frame"]
        selected_p1 = record.get("selected_p1")
        for actor in record.get("actors", []):
            if args.selected_p1_only and actor.get("address") != selected_p1:
                continue
            family = SCRIPTS.get(actor.get("animation_script"))
            if family is None:
                continue
            direction = actor.get("direction")
            if not isinstance(direction, int) or not 0 <= direction <= 7:
                continue
            key = (family, direction)
            samples[key] += 1
            velocities[key].append(math.hypot(actor["vx"], actor["vy"]))
            address = actor["address"]
            prior = previous.get(address)
            if prior is not None:
                prior_frame, prior_x, prior_y, prior_family, prior_direction = prior
                elapsed = frame - prior_frame
                if elapsed > 0 and prior_family == family and prior_direction == direction:
                    distance_per_frame = math.hypot(actor["x"] - prior_x, actor["y"] - prior_y) / elapsed
                    # Positions are stored in the ROM's match-space.  A jump this
                    # large is a spawn/reset/camera discontinuity, not locomotion.
                    if distance_per_frame <= 16:
                        deltas[key].append(distance_per_frame)
                    else:
                        rejected += 1
            previous[address] = (frame, actor["x"], actor["y"], family, direction)

    families: dict[str, dict[str, object]] = {}
    for family in ("walking", "running"):
        directions: dict[str, object] = {}
        for direction in range(8):
            key = (family, direction)
            directions[str(direction)] = {
                "actor_samples": samples[key],
                "adjacent_position_samples": len(deltas[key]),
                "position_delta_per_emulated_frame": quantiles(deltas[key]),
                "moving_position_delta_per_emulated_frame": quantiles(
                    [delta for delta in deltas[key] if delta > 0]
                ),
                "raw_velocity_word_magnitude": quantiles(velocities[key]),
            }
        families[family] = directions

    payload = {
        "schema_version": 1,
        "source": {"trace": str(args.trace).replace("\\", "/"), "capture": "passive natural-play telemetry"},
        "actor_scope": "selected_p1" if args.selected_p1_only else "all_capturable_actors",
        "movement_scripts": {str(pointer): name for pointer, name in SCRIPTS.items()},
        "units": {
            "position_delta_per_emulated_frame": "ROM match-coordinate units; no Canvas conversion applied",
            "raw_velocity_word_magnitude": "magnitude of signed words recorded from actor+$46/$48",
        },
        "teleport_or_reset_deltas_rejected": rejected,
        "families": families,
        "limitations": [
            "Position deltas are native ROM match-coordinate units and are not converted to Canvas or screen pixels.",
            "A movement script identifies an observed animation family, not a complete input, acceleration, collision, or possession state.",
            "The all-actor report includes AI and non-selected actors; the selected-player report is the appropriate input for future control calibration.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
