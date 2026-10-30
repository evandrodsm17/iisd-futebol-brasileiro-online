"""Validate raw native action OAM capture without inferring actor-to-OAM slots."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def validate(trace: Path) -> dict:
    rows, errors, scripts = 0, [], Counter()
    for n, line in enumerate(trace.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        rows += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"line {n}: invalid JSON: {error}")
            continue
        if row.get("schema") != "issd-native-action-oam/v1":
            errors.append(f"line {n}: unsupported schema")
            continue
        actor = row.get("actor", {})
        if not all(isinstance(actor.get(key), int) for key in
                   ("address", "animation_script", "descriptor", "direction", "pose")):
            errors.append(f"line {n}: missing actor metadata")
        else:
            scripts[f"${actor['animation_script']:04X}"] += 1
        for key, size in (("oam_mirror", 544), ("oam_ppu", 544), ("vram", 65536)):
            name = row.get(key)
            if name is None and key == "oam_ppu":
                continue
            if not isinstance(name, str):
                errors.append(f"line {n}: missing {key}")
                continue
            path = trace.parent / name
            if not path.is_file() or path.stat().st_size != size:
                errors.append(f"line {n}: {key} missing or wrong size ({name})")
        cgram = row.get("cgram")
        if not isinstance(cgram, str) or not (trace.parent / cgram).is_file():
            errors.append(f"line {n}: missing CGRAM")
        else:
            try:
                data = bytes.fromhex("".join((trace.parent / cgram).read_text(encoding="utf-8").split()))
                if len(data) != 512:
                    errors.append(f"line {n}: CGRAM must decode to 512 bytes")
            except (ValueError, UnicodeError):
                errors.append(f"line {n}: invalid CGRAM hex")
        screen = row.get("screenshot")
        if screen is not None and not (trace.parent / screen).is_file():
            errors.append(f"line {n}: missing screenshot")
    return {
        "schema": "issd-native-action-oam-validation/v1",
        "total_records": rows,
        "scripts": dict(sorted(scripts.items())),
        "errors": errors,
        "valid": not errors and rows > 0,
        "limitations": "File integrity only; snapshot does not yet prove which native OAM slots belong to an actor.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.trace)
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
