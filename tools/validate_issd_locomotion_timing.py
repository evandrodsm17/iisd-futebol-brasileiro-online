"""Verify the ROM-decoded walking and running timing tables."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "walking": {"kind": "constant", "ticks": 3},
    "running": {"kind": "per_frame", "ticks": [4, 3, 3, 3, 4, 3, 3, 3]},
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    cycles = payload["cycles"]
    for name, expected in EXPECTED.items():
        actual = cycles[name]["timing"]
        if actual != expected:
            raise SystemExit(f"{name} timing mismatch: {actual!r} != {expected!r}")
    print("locomotion timing: OK")


if __name__ == "__main__":
    main()
