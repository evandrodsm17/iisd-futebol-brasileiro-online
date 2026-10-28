"""Validate native tile-base fields in ISSD JSONL OAM captures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def actors(record: dict) -> list[dict]:
    if "actor" in record:
        return [record["actor"]]
    return record.get("actors", [])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line]
    checked = legacy = mismatches = 0
    examples: list[dict] = []
    for record in records:
        for actor in actors(record):
            parts = actor.get("parts", [])
            if not parts:
                continue
            if "object_field_02" not in actor or any("geometry_tile" not in part for part in parts):
                legacy += 1
                continue
            base = actor["object_field_02"]
            for part in parts:
                checked += 1
                expected = (part["geometry_tile"] + base) & 0xFF
                if part.get("tile") != expected:
                    mismatches += 1
                    if len(examples) < 12:
                        examples.append({
                            "address": actor.get("address"),
                            "geometry_tile": part["geometry_tile"],
                            "object_field_02": base,
                            "tile": part.get("tile"),
                            "expected_tile": expected,
                        })
    payload = {
        "trace": str(args.trace).replace("\\", "/"),
        "checked_parts": checked,
        "legacy_actors": legacy,
        "mismatches": mismatches,
        "examples": examples,
        "status": "legacy-trace" if not checked else ("ok" if not mismatches else "mismatch"),
    }
    print(json.dumps(payload, indent=2))
    if mismatches:
        raise SystemExit("native OAM tile-base mismatch")


if __name__ == "__main__":
    main()
