"""Summarize unlabeled roster appearance-nibble candidates without naming them."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    players = [player for team in catalog.get("teams", []) for player in team.get("players", [])]
    if len(players) != 720:
        raise ValueError(f"expected 720 roster players, found {len(players)}")
    high = Counter(player["appearance"]["skin_tone"] for player in players)
    low = Counter(player["appearance"]["hair_style"] for player in players)
    payload = {
        "schema_version": 1,
        "source": {"catalog": str(args.catalog), "record_byte": "06", "player_count": len(players)},
        "candidate_nibbles": {
            "high": {str(value): high[value] for value in sorted(high)},
            "low": {str(value): low[value] for value in sorted(low)},
        },
        "capture_priority": {
            "high_values": sorted(high),
            "low_values": sorted(low),
            "rule": "capture at least one runtime player for every observed high/low candidate value before assigning a visual meaning",
        },
        "limitations": [
            "Catalog labels skin_tone and hair_style are decoding candidates, not runtime-proven visual selectors.",
            "Counts do not prove which OBJ tiles, palettes, or actor fields each candidate controls.",
            "This artifact does not modify player graphics in the browser.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
