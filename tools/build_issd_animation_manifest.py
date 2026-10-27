"""Build the browser-facing animation registry from resolved live evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_map", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = json.loads(args.asset_map.read_text(encoding="utf-8"))
    states = []
    for script in source["scripts"]:
        assets = sorted({frame["asset"] for frame in script["frames"] if frame.get("asset")})
        frames = [{key: frame[key] for key in ("descriptor", "samples", "pose", "graphics_source", "detail", "asset") if key in frame}
                  for frame in script["frames"]]
        states.append({
            "script": script["script"],
            "observed_samples": script["samples"],
            "directions": script["directions"],
            "assets": assets,
            "frames": frames,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "schema": "issd-runtime-animation-registry/v1",
        "evidence": source["evidence"],
        "trace_valid_samples": source["trace_valid_samples"],
        "states": states,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
