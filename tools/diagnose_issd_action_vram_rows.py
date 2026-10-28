"""Report whether a captured action trace can validly compare dynamic VRAM rows."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--script", type=lambda value: int(value, 0), required=True)
    args = parser.parse_args()
    if not args.rom.is_file():
        raise FileNotFoundError(args.rom)
    rows = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line]
    rows = [row for row in rows if row["actor"]["animation_script"] == args.script]
    if not rows:
        raise ValueError(f"trace lacks script ${args.script:04X}")

    print(json.dumps({
        "script": f"$82:{args.script:04X}",
        "compared_tiles": 0,
        "status": "awaiting-direct-page-binding",
        "trace_has_object_field_02": all("object_field_02" in row["actor"] for row in rows),
        "reason": "CODE_84:E6C7 uses direct-page $02 for the dynamic VRAM destination. The old trace lacks actor+$02; the updated collector preserves it, but a debugger trace must still bind that field to direct-page $02 before a tile-level comparison is valid.",
    }, indent=2))


if __name__ == "__main__":
    main()
